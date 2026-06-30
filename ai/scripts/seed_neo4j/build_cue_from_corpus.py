"""
build_cue_from_corpus.py — Xây dựng sense-specific cues từ Tatoeba corpus.

Thay thế DOMAIN_CUE_SEEDS (shared per domain) bằng corpus-derived cues (per Lexeme).

Tại sao tốt hơn?
  - Domain seeds: tất cả technology senses share CÙNG cue set → cueMatch bằng nhau
  - Corpus cues:  mỗi Lexeme có cue riêng từ ngữ liệu thực → sense-discriminative

Algorithm:
  1. Load tất cả Lexeme surfaces vào Aho-Corasick automaton (multi-pattern matching)
  2. Đọc 248k câu tiếng Nhật từ Tatoeba, tìm tất cả surfaces trong mỗi câu
  3. Build co-occurrence counter: lexeme_surface → Counter{co_surface: count}
  4. Với mỗi Sense chuyên ngành:
     a. Lấy top-K co-occurring surfaces của Lexeme đó làm cues
     b. Nếu không đủ MIN_CUES → fallback sang domain seeds (kết hợp)
  5. Ghi ra cue_mapping_raw.json (ghi đè file cũ)

Output: data/neo4j/cue_mapping_raw.json (same format, better quality)
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from tqdm import tqdm

from config import (
    NEO4J_DIR, DOMAIN_CUE_SEEDS, MIN_CUES_PER_SENSE,
)

TATOEBA_SENTENCES = (
    Path(__file__).parent.parent / "seed_dictionary" / "data" / "raw" / "sentences.csv"
)
TOP_K_CUES = 20          # Lấy tối đa 20 co-occurring per Lexeme
MIN_COOCCUR_COUNT = 1    # Ngưỡng tối thiểu để tính là cue

try:
    import ahocorasick
    HAS_AHOCORASICK = True
except ImportError:
    HAS_AHOCORASICK = False
    print("WARNING: pyahocorasick chưa cài → dùng substring matching (chậm hơn)")


# ── Step 1: Build Aho-Corasick automaton ─────────────────────────────────────

def build_automaton(surfaces: list[str]):
    """Xây dựng Aho-Corasick automaton từ tập surfaces."""
    if not HAS_AHOCORASICK:
        return None

    A = ahocorasick.Automaton()
    for idx, surface in enumerate(surfaces):
        if len(surface) >= 2:  # Bỏ qua surface 1 ký tự (quá ngắn, nhiều FP)
            A.add_word(surface, (idx, surface))
    A.make_automaton()
    return A


def find_surfaces_in_text(text: str, automaton, surfaces_set: set[str]) -> set[str]:
    """Tìm tất cả surfaces xuất hiện trong 1 câu."""
    if automaton is not None:
        # Aho-Corasick: O(text_length + matches)
        return {surface for _, (_, surface) in automaton.iter(text)}
    else:
        # Fallback: substring matching
        return {s for s in surfaces_set if len(s) >= 2 and s in text}


# ── Step 2: Load Japanese sentences ──────────────────────────────────────────

def load_japanese_sentences(path: Path) -> list[str]:
    """Đọc câu tiếng Nhật từ Tatoeba sentences.csv."""
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {path}\n"
            f"  Chạy: cd ai/scripts/seed_dictionary && bash download_sources.sh"
        )

    sentences = []
    print(f"Loading Japanese sentences từ {path.name} ...")
    with open(path, encoding="utf-8") as f:
        for line in tqdm(f, desc="  Reading", unit="line", total=13_451_914):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[1] == "jpn":
                text = parts[2].strip()
                if text:
                    sentences.append(text)

    print(f"  → {len(sentences):,} Japanese sentences loaded")
    return sentences


# ── Step 3: Build co-occurrence ───────────────────────────────────────────────

def build_cooccurrence(
    sentences: list[str],
    surfaces: list[str],
) -> dict[str, Counter]:
    """
    Với mỗi surface, đếm số câu mà surface đó co-occur với surface khác.

    Returns:
        dict[surface → Counter{co_surface: count}]
    """
    automaton = build_automaton(surfaces)
    surfaces_set = set(surfaces)

    # co_occ[s1][s2] = số câu mà s1 và s2 cùng xuất hiện
    co_occ: dict[str, Counter] = defaultdict(Counter)

    print(f"\nBuilding co-occurrence từ {len(sentences):,} câu ...")
    for sent in tqdm(sentences, desc="  Processing", unit="sent"):
        found = find_surfaces_in_text(sent, automaton, surfaces_set)
        if len(found) < 2:
            continue  # Cần ≥2 surfaces mới có co-occurrence
        for s in found:
            co_occ[s].update(found - {s})

    print(f"  → Co-occurrence built cho {len(co_occ):,} surfaces")
    return co_occ


# ── Step 4: Generate sense-specific cue mapping ───────────────────────────────

def build_cue_from_corpus(out_dir: Path = NEO4J_DIR) -> list[dict]:
    """
    Đọc lexemes/senses, build corpus co-occurrence, tạo cue mapping.
    Ghi đè data/neo4j/cue_mapping_raw.json.
    """
    lex_path   = out_dir / "lexemes_raw.json"
    sense_path = out_dir / "senses_raw.json"

    if not lex_path.exists():
        raise FileNotFoundError("Cần chạy extract_from_jmdict.py trước.")

    with open(lex_path, encoding="utf-8") as f:
        lexemes: list[dict] = json.load(f)
    with open(sense_path, encoding="utf-8") as f:
        senses: list[dict] = json.load(f)

    surfaces = [l["surface"] for l in lexemes]
    lexeme_surfaces: set[str] = set(surfaces)
    lexeme_id_to_surface: dict[str, str] = {l["lexemeId"]: l["surface"] for l in lexemes}

    print(f"Lexemes: {len(lexemes):,} | Senses: {len(senses):,}")

    # ── Load corpus ───────────────────────────────────────────────────────────
    sentences = load_japanese_sentences(TATOEBA_SENTENCES)

    # ── Build co-occurrence ───────────────────────────────────────────────────
    co_occ = build_cooccurrence(sentences, surfaces)

    # ── Build domain-peers: domain → list of surfaces với ít nhất 1 sense đó ─
    # Dùng làm fallback pool khi corpus coverage thấp
    print("\nBuilding domain-peers fallback pool ...")
    domain_peer_surfaces: dict[str, list[str]] = defaultdict(list)
    for s in senses:
        if s["domainKey"] != "general":
            surf = lexeme_id_to_surface.get(s["lexemeId"], "")
            if surf:
                domain_peer_surfaces[s["domainKey"]].append(surf)
    # Deduplicate và shuffle để đa dạng
    import random
    random.seed(42)
    for domain in domain_peer_surfaces:
        peers = list(dict.fromkeys(domain_peer_surfaces[domain]))  # deduplicate giữ thứ tự
        random.shuffle(peers)
        domain_peer_surfaces[domain] = peers

    for domain, peers in domain_peer_surfaces.items():
        print(f"  {domain:12s}: {len(peers):,} peer surfaces")

    # ── Generate cue mapping ──────────────────────────────────────────────────
    cue_mapping: list[dict] = []
    stats = {
        "corpus_only":   0,
        "corpus_padded": 0,
        "peers_only":    0,
        "still_zero":    0,
    }

    for sense in senses:
        domain_key = sense["domainKey"]
        if domain_key == "general":
            continue

        sense_id    = sense["senseId"]
        lexeme_id   = sense["lexemeId"]
        own_surface = lexeme_id_to_surface.get(lexeme_id, "")

        # ── Bước 1: Corpus cues ───────────────────────────────────────────────
        corpus_cues: list[str] = []
        if own_surface in co_occ:
            top = co_occ[own_surface].most_common(TOP_K_CUES)
            corpus_cues = [
                surf for surf, cnt in top
                if surf != own_surface and cnt >= MIN_COOCCUR_COUNT
            ]

        combined: list[str] = list(dict.fromkeys(corpus_cues))

        if len(combined) >= MIN_CUES_PER_SENSE:
            stats["corpus_only"] += 1
        else:
            # ── Bước 2: Fallback — domain peers ──────────────────────────────
            # Lấy các Lexeme CÙNG DOMAIN làm cues bổ sung
            corpus_set = set(corpus_cues)
            peers = domain_peer_surfaces.get(domain_key, [])
            for peer_surf in peers:
                if peer_surf not in corpus_set and peer_surf != own_surface:
                    combined.append(peer_surf)
                if len(combined) >= MIN_CUES_PER_SENSE:
                    break

            if len(combined) >= MIN_CUES_PER_SENSE:
                if corpus_cues:
                    stats["corpus_padded"] += 1
                else:
                    stats["peers_only"] += 1
            else:
                stats["still_zero"] += 1

        # Giữ tối đa TOP_K_CUES cues
        final_cues = combined[:TOP_K_CUES]

        for surf in final_cues:
            cue_mapping.append({"senseId": sense_id, "cueSurface": surf})

    # ── Stats ─────────────────────────────────────────────────────────────────
    specialized_senses = sum(1 for s in senses if s["domainKey"] != "general")
    avg_cues = len(cue_mapping) / max(specialized_senses, 1)

    print(f"\n── Kết quả cue mapping (corpus-derived) ──")
    print(f"  Specialized senses:            {specialized_senses:,}")
    print(f"  ✅ Corpus only (≥{MIN_CUES_PER_SENSE} cue):  {stats['corpus_only']:,}")
    print(f"  🔀 Corpus + peers padded:      {stats['corpus_padded']:,}")
    print(f"  ⚠️  Peers only (no corpus):    {stats['peers_only']:,}")
    print(f"  ❌ Still zero:                 {stats['still_zero']:,}")
    print(f"  Total cue rows:                {len(cue_mapping):,}")
    print(f"  Average cues/sense:            {avg_cues:.1f}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = out_dir / "cue_mapping_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cue_mapping, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved: {out_path}")

    # ── Sample để kiểm tra ────────────────────────────────────────────────────
    print("\n── Sample cues (corpus-derived) ──")
    surface_to_lexid = {l["surface"]: l["lexemeId"] for l in lexemes}
    sample_surfaces = ["半導体", "データ", "治療", "市場", "音楽", "研究", "コンピュータ", "薬"]
    cue_by_sense: dict[str, list[str]] = defaultdict(list)
    for c in cue_mapping:
        cue_by_sense[c["senseId"]].append(c["cueSurface"])

    for surf in sample_surfaces:
        lex_id = surface_to_lexid.get(surf)
        if not lex_id:
            continue
        sense_sample = next(
            (s for s in senses if s["lexemeId"] == lex_id and s["domainKey"] != "general"),
            None
        )
        if not sense_sample:
            continue
        sid = sense_sample["senseId"]
        sample_cues = cue_by_sense[sid][:10]
        # Kiểm tra có phải corpus cues hay peers
        corpus_flag = "📖" if surf in co_occ else "🌱"
        print(f"  {corpus_flag} [{surf}] ({sense_sample['domainKey']}) → {sample_cues}")

    return cue_mapping


if __name__ == "__main__":
    build_cue_from_corpus()
