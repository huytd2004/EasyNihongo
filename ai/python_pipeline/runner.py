"""
Pipeline stateless cho dịch đoạn văn chuyên ngành Nhật → Việt.

Nguyên tắc (theo schema-neo4j.md):
- Neo4j chỉ query read-only theo token surface.
- Không tạo Sentence/Token node trong Neo4j.
- Tokenization, domain detection, sense ranking hoàn toàn in-memory.
- Lịch sử bản dịch (nếu cần) lưu PostgreSQL ở backend.
"""

import json
import re

from .neo4j_client import Neo4jClient
from .ranker import Ranker
from .prompt_builder import build_prompt
from .llm_client import LLMClient

# ── Stopword POS tags (MeCab) ─────────────────────────────────────────────────
STOP_POS = {'助詞', '助動詞', '記号', '補助記号', '空白'}


def _tokenize_in_memory(text: str) -> list[dict]:
    """
    Tokenize văn bản Nhật. Thứ tự ưu tiên:
      1. SudachiPy  — tốt nhất, xử lý katakana compound words
      2. MeCab      — fallback nếu có
      3. Regex      — fallback đơn giản, tách theo ký tự Japanese
    KHÔNG tạo bất kỳ node Neo4j nào.
    """
    # ── Try SudachiPy ─────────────────────────────────────────────────────────
    try:
        from sudachipy import tokenizer as sudachi_tokenizer, dictionary as sudachi_dict
        _tokenizer_obj = sudachi_dict.Dictionary().create()
        # Mode B (standard): tách compound katakana thành units đơn lẻ
        # Ví dụ: クラウドコンピューティング → クラウド + コンピューティング
        # Mode C (long unit) giữ nguyên compound nhưng graph chỉ index từ đơn
        _mode = sudachi_tokenizer.Tokenizer.SplitMode.B

        SUDACHI_STOP_POS = {'助詞', '助動詞', '補助記号', '空白', '感動詞'}
        tokens = []
        position = 0
        seen = set()  # deduplicate cùng surface ở cùng vị trí
        for m in _tokenizer_obj.tokenize(text, _mode):
            surface = m.surface()
            pos     = m.part_of_speech()[0]
            reading = m.reading_form() or surface
            if surface.strip() and pos not in SUDACHI_STOP_POS:
                if not all(c in '、。！？・「」『』【】（）…' for c in surface):
                    tokens.append({
                        'surface':  surface,
                        'reading':  reading,
                        'pos':      pos,
                        'position': position,
                    })
                    position += 1
        return tokens
    except Exception:
        pass

    # ── Try MeCab ─────────────────────────────────────────────────────────────
    try:
        import MeCab
        tagger = MeCab.Tagger()
        tokens = []
        position = 0
        node = tagger.parseToNode(text)
        while node:
            surface  = node.surface
            features = node.feature.split(',')
            pos      = features[0] if features else ''
            if surface and pos not in STOP_POS:
                tokens.append({
                    'surface':  surface,
                    'reading':  features[7] if len(features) > 7 else surface,
                    'pos':      pos,
                    'position': position,
                })
                position += 1
            node = node.next
        return tokens
    except Exception:
        pass

    # ── Regex fallback: tách theo boundary giữa CJK và Latin/Katakana ─────────
    # Tốt hơn nhiều so với text.split() cho tiếng Nhật
    import re
    # Pattern: giữ lại các chuỗi liên tục (Kanji, Katakana, Hiragana, Latin, số)
    pattern = re.compile(
        r'[ァ-ヶー]+|'      # Katakana (bao gồm compound)
        r'[一-龯々]+|'       # Kanji
        r'[ぁ-ん]+|'         # Hiragana
        r'[A-Za-z0-9ａ-ｚＡ-Ｚ０-９]+',  # Latin + fullwidth
    )
    return [
        {'surface': m.group(), 'reading': m.group(), 'pos': 'unknown', 'position': i}
        for i, m in enumerate(pattern.finditer(text))
        if m.group().strip()
    ]


def _detect_domains_from_graph(
    graph_evidence: list[dict],
    neighbor_surfaces: set[str],
    confidence_threshold: float = 0.30,
) -> list[str]:
    """
    Phát hiện domain bằng FREQUENCY VOTE:
    Đếm số token trong văn bản có sense thuộc từng domain,
    rồi chọn domain có nhiều token vote nhất.

    Tại sao tốt hơn keyword matching:
      - Không cần hardcode từ khoá
      - Tự động scale theo từ vựng thực trong đoạn văn
      - Word có nhiều domain chỉ đóng góp 1 vote/domain (không bị inflate)

    Tại sao tốt hơn cue-ratio:
      - Không phụ thuộc chất lượng cue data
      - Ổn định hơn khi cue coverage thấp

    Algorithm:
      1. Với mỗi (token, domain) trong graph_evidence:
         → token_domain_votes[token].add(domain)
      2. Tổng hợp: domain_vote_count[domain] = số token distinct vote cho domain đó
      3. Bỏ qua 'general' và 'domain_general' vì chúng có mặt ở hầu hết token
      4. Chọn domain có vote_count >= max_vote * threshold_ratio

    Params:
        graph_evidence       : kết quả từ batch_query_by_surfaces
        neighbor_surfaces    : (không dùng trong frequency vote, giữ signature tương thích)
        confidence_threshold : tỉ lệ so với domain cao nhất (default 0.15 = 15%)
                               Ví dụ: tech=10 votes, medicine=2 votes, threshold=0.15
                               → medicine >= 10*0.15=1.5 → cả 2 được chọn

    Returns:
        list[str] domain được detect (ví dụ ['domain_technology'])
        Mặc định ['general'] nếu không detect được gì.
    """
    from collections import defaultdict

    # token → set of domains nó có sense thuộc về (chỉ non-general)
    token_domains: dict[str, set[str]] = defaultdict(set)

    for row in graph_evidence:
        token  = row.get('token', '')
        domain = row.get('domain', '')
        if not token or not domain:
            continue
        # Bỏ qua general — nó xuất hiện ở hầu hết mọi từ, không discriminative
        if domain in ('general', 'domain_general'):
            continue
        token_domains[token].add(domain)

    if not token_domains:
        # Không có token nào có sense chuyên ngành → general
        return ['general']

    # domain_vote[domain] = số token distinct có sense thuộc domain đó
    domain_vote: dict[str, int] = defaultdict(int)
    for token, domains in token_domains.items():
        for domain in domains:
            domain_vote[domain] += 1

    if not domain_vote:
        return ['general']

    max_votes = max(domain_vote.values())
    min_votes = max(1, max_votes * confidence_threshold)

    # Chọn tất cả domain có votes >= ngưỡng, sort giảm dần
    detected = sorted(
        [d for d, v in domain_vote.items() if v >= min_votes],
        key=lambda d: -domain_vote[d],
    )

    return detected if detected else ['general']


def _detect_domains_fallback(surfaces: list[str]) -> list[str]:
    """
    Fallback nhanh khi chưa có graph evidence (pass 1).
    Dùng heuristic đơn giản: tỉ lệ từ katakana/kanji dài trong text.
    Trả về ['general'] nếu không detect được gì — Neo4j sẽ trả về ALL senses
    và pass 2 sẽ detect chính xác hơn từ graph evidence.
    """
    # Heuristic: nếu có nhiều từ katakana dài (≥3 ký tự) → likely tech/academic
    long_katakana = [
        s for s in surfaces
        if len(s) >= 3 and all('\u30A0' <= c <= '\u30FF' for c in s)
    ]
    if len(long_katakana) >= 2:
        return ['domain_technology', 'domain_academic']
    return ['general']


def _parse_llm_json(raw_text: str) -> tuple[str, list[dict]]:
    """
    Parse JSON output từ LLM. Xử lý trường hợp LLM bọc trong markdown code block.
    Returns (translation, notes).
    """
    text = raw_text.strip()
    # Strip markdown code block nếu có
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed.get('translation', ''), parsed.get('notes', [])
    except json.JSONDecodeError:
        # Fallback 1: Try to extract the translation field using regex
        match = re.search(r'"translation"\s*:\s*"((?:[^"\\]|\\.)*)', text)
        if match:
            extracted = match.group(1)
            try:
                extracted = json.loads(f'"{extracted}"')
            except Exception:
                extracted = extracted.replace('\\"', '"')
            return extracted, []

        # Fallback 2: treat toàn bộ text là bản dịch
        return text, []



class Pipeline:
    def __init__(self, neo4j_client=None, ranker=None, llm=None):
        self.neo = neo4j_client or Neo4jClient()
        self.ranker = ranker or Ranker()
        self.llm = llm or LLMClient()

    def translate(self, input_text: str) -> dict:
        """
        Dịch đoạn văn chuyên ngành Nhật → Việt (stateless).

        Returns:
            {
              "translation":     str,
              "keyVocabulary":   list[dict],
              "notes":           list[dict],
              "detectedDomains": list[str],
            }
        """
        # ── Bước 1: Tokenize in-memory ────────────────────────────────────────
        tokens = _tokenize_in_memory(input_text)
        surfaces = [t['surface'] for t in tokens]
        unique_surfaces = list(dict.fromkeys(surfaces))  # preserve order, deduplicate
        neighbor_surfaces = set(surfaces)

        # ── Bước 2a: Query Neo4j pass 1 — dùng ['general'] để lấy tất cả senses
        #    (vì chưa biết domain, lấy hết để có cue data cho bước detect)
        graph_evidence = self.neo.batch_query_by_surfaces(unique_surfaces, ['general'])

        # ── Bước 2b: Detect domain từ graph cue evidence (chính xác hơn keyword)
        detected_domains = _detect_domains_from_graph(
            graph_evidence,
            neighbor_surfaces,
            confidence_threshold=0.30,
        )

        # ── Bước 2c: Nếu graph trả về ít data → fallback heuristic
        if not graph_evidence:
            detected_domains = _detect_domains_fallback(surfaces)

        # ── Bước 3: Re-query Neo4j với domain đã detect (lấy đúng senses) ──────
        # Chỉ re-query nếu detect được domain cụ thể (không phải 'general')
        if detected_domains != ['general']:
            graph_evidence = self.neo.batch_query_by_surfaces(unique_surfaces, detected_domains)

        # ── Bước 4: Rank senses in-memory ────────────────────────────────────
        ranked_senses, key_vocabulary = self.ranker.rank(graph_evidence, detected_domains)

        # ── Bước 5: Build prompt ──────────────────────────────────────────────
        prompt = build_prompt(input_text, ranked_senses, detected_domains)

        # ── Bước 6: LLM translate ─────────────────────────────────────────────
        resp = self.llm.complete(prompt, model='llama-3.1-8b-instant', max_tokens=2048)
        translation, notes = _parse_llm_json(resp.get('text', ''))

        # ── Bước 7: Format output ─────────────────────────────────────────────
        return {
            'translation':     translation,
            'keyVocabulary':   key_vocabulary,
            'notes':           notes,
            'detectedDomains': detected_domains,
            'model':           resp.get('model', 'unknown'),
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description='Stateless translation pipeline')
    parser.add_argument('--text', required=True, help='Đoạn văn tiếng Nhật cần dịch')
    parser.add_argument('--json', action='store_true', help='Xuất JSON thay vì plain text')
    args = parser.parse_args()

    p = Pipeline()
    out = p.translate(args.text)

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(out['translation'])
        if out.get('keyVocabulary'):
            print('\n--- Từ vựng quan trọng ---')
            for kv in out['keyVocabulary']:
                score_str = f"score={kv.get('score', 0):.2f}"
                print(f"  {kv['surface']} ({kv.get('reading', '')}) [{kv.get('domain', '')}] → {kv.get('glossVi', '')}  {score_str}")
        if out.get('notes'):
            print('\n--- Ghi chú ---')
            for n in out['notes']:
                print(f"  [{n.get('type')}] {n.get('token')}: {n.get('content')}")


if __name__ == '__main__':
    main_cli()
