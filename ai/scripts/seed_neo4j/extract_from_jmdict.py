"""
extract_from_jmdict.py — Trích xuất Lexeme + Sense từ JMdict JSON cho Neo4j.

Chiến lược:
1. Load jmdict-eng.json (đã có từ seed_dictionary pipeline).
2. Với mỗi word entry, map misc tags → domain.
3. Chỉ giữ word có ≥ 1 sense chuyên ngành (domain != general).
4. Để xử lý polysemy, gom tất cả senses (kể cả general) của word đó.
5. Output: lexemes_raw.json, senses_raw.json
"""
import json
import re
import uuid
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

from config import (
    JMDICT_JSON, NEO4J_DIR, MISC_TO_DOMAIN,
    MIN_SENSES_FOR_POLYSEMY,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

POS_MAP = {
    "noun":                    "n",
    "suru verb":               "v",
    "godan verb":              "v",
    "ichidan verb":            "v",
    "transitive verb":         "v",
    "intransitive verb":       "v",
    "i-adjective":             "adj",
    "na-adjective":            "adj",
    "adverb":                  "adv",
}


def _simplify_pos(pos_list: list[str]) -> str:
    """Map JMdict POS list → n|v|adj|adv|other."""
    for pos in pos_list:
        for key, val in POS_MAP.items():
            if key in pos.lower():
                return val
    return "other"


def _safe_id(surface: str) -> str:
    """Tạo lexemeId an toàn từ surface (bỏ ký tự đặc biệt)."""
    clean = re.sub(r"[^\w\u3000-\u9fff\uff00-\uffef]", "_", surface)
    return f"lex_{clean}"


def _sense_id(lexeme_id: str, domain: str, idx: int) -> str:
    return f"{lexeme_id}__{domain}__{idx}"


def _extract_field_tags(sense: dict) -> list[str]:
    """
    Lấy field tags từ 1 sense dict.
    JMdict dùng 'field' (không phải 'misc') để chứa domain/topic labels.
    Ví dụ: comp, med, math, food, law, music, sports...
    """
    return sense.get("field", [])


def _map_field_to_domain(field_tags: list[str]) -> str:
    """Trả về domain đầu tiên match trong MISC_TO_DOMAIN, mặc định 'general'."""
    for tag in field_tags:
        if tag in MISC_TO_DOMAIN:
            return MISC_TO_DOMAIN[tag]
    return "general"


def _extract_gloss_en(sense: dict) -> str:
    """Lấy gloss tiếng Anh (tối đa 3), join bằng '; '."""
    glosses = [
        g["text"] for g in sense.get("gloss", [])
        if g.get("lang") == "eng"
    ]
    return "; ".join(glosses[:3]) if glosses else ""


def _extract_xrefs(sense: dict) -> list[str]:
    """
    Lấy cross-references từ sense để dùng làm cue candidates.
    JMdict có 'related' và 'antonym' fields (list of xref strings).
    """
    refs = []
    for field in ("related", "antonym"):
        for xref in sense.get(field, []):
            # xref có thể là string "word" hoặc list ["word", "sense_num"]
            if isinstance(xref, str):
                refs.append(xref)
            elif isinstance(xref, list) and xref:
                refs.append(str(xref[0]))
    return refs


# ── Main extraction ───────────────────────────────────────────────────────────

def extract_lexemes_and_senses(
    jmdict_path: Path = JMDICT_JSON,
    out_dir: Path = NEO4J_DIR,
    jlpt_lookup: dict[str, str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    Đọc JMdict JSON và trả về (lexemes, senses).

    Args:
        jmdict_path: Đường dẫn đến jmdict-eng.json
        out_dir: Thư mục output
        jlpt_lookup: Optional dict {surface: jlpt_level} từ seed_dictionary

    Returns:
        (lexemes, senses) — đã lọc chuyên ngành
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading JMdict from {jmdict_path} ...")
    if not jmdict_path.exists():
        # Thử đường dẫn tương đối từ seed_dictionary
        alt = jmdict_path.parent.parent / "seed_dictionary" / "data" / "raw" / "jmdict-eng.json"
        if alt.exists():
            jmdict_path = alt
            print(f"  → Found at {jmdict_path}")
        else:
            raise FileNotFoundError(
                f"Không tìm thấy JMdict JSON tại {jmdict_path}\n"
                f"  Chạy: cd ai/scripts/seed_dictionary && bash download_sources.sh"
            )

    with open(jmdict_path, encoding="utf-8") as f:
        data = json.load(f)

    words = data.get("words", [])
    print(f"Total JMdict entries: {len(words):,}")

    lexemes: list[dict] = []
    senses: list[dict] = []

    skipped_no_specialized = 0
    skipped_no_gloss = 0

    for word in tqdm(words, desc="Extracting", unit="word"):
        # ── Surface & Reading ────────────────────────────────────
        kanji_forms = word.get("kanji", [])
        kana_forms  = word.get("kana", [])
        if not kana_forms:
            continue  # Cần ít nhất kana

        surface = kanji_forms[0]["text"] if kanji_forms else kana_forms[0]["text"]
        reading = kana_forms[0]["text"] if kana_forms else None
        if surface == reading:
            reading = None  # Không cần lưu reading nếu trùng surface

        # ── POS ──────────────────────────────────────────────────
        all_pos: list[str] = []
        for s in word.get("sense", []):
            all_pos.extend(s.get("partOfSpeech", []))
        pos = _simplify_pos(all_pos)

        # ── JLPT ─────────────────────────────────────────────────
        jlpt_level: int | None = None
        if jlpt_lookup:
            raw_level = jlpt_lookup.get(surface) or jlpt_lookup.get(reading or "")
            if raw_level:
                try:
                    jlpt_level = int(raw_level.replace("N", ""))
                except ValueError:
                    pass

        # ── Process senses ───────────────────────────────────────
        word_senses: list[dict] = []
        has_specialized = False

        for idx, s in enumerate(word.get("sense", [])):
            gloss_en = _extract_gloss_en(s)
            if not gloss_en:
                continue

            field_tags = _extract_field_tags(s)
            domain     = _map_field_to_domain(field_tags)
            xrefs     = _extract_xrefs(s)

            if domain != "general":
                has_specialized = True

            lexeme_id = _safe_id(surface)
            sense_id  = _sense_id(lexeme_id, domain, idx)

            word_senses.append({
                "senseId":   sense_id,
                "lexemeId":  lexeme_id,
                "glossEn":   gloss_en,
                "glossVi":   "",          # Sẽ fill ở translate_vi.py
                "domain":    f"domain_{domain}",
                "domainKey": domain,
                "xrefs":     xrefs,       # Dùng trong build_cue_mapping.py
            })

        # ── Filter: chỉ giữ word có sense chuyên ngành ───────────
        if not has_specialized:
            skipped_no_specialized += 1
            continue

        if not word_senses:
            skipped_no_gloss += 1
            continue

        lexeme_id = _safe_id(surface)
        lexemes.append({
            "lexemeId": lexeme_id,
            "surface":  surface,
            "reading":  reading or "",
            "pos":      pos,
            "jlpt":     jlpt_level or "",
        })

        senses.extend(word_senses)

    # ── Post-processing: Polysemy filter ─────────────────────────────────────
    # Chỉ giữ Lexeme có ≥ 2 sense với domain KHÁC NHAU (true polysemy).
    # Đây là điều kiện cốt lõi: rank_sense chỉ có ý nghĩa với từ đa nghĩa.
    print("\n  Applying polysemy filter (≥2 senses with different domains)...")

    from collections import defaultdict as _dd
    # Group senses by lexemeId
    sense_by_lex: dict[str, list[dict]] = _dd(list)
    for s in senses:
        sense_by_lex[s["lexemeId"]].append(s)

    # Filter Lexemes
    polysemy_lexeme_ids: set[str] = set()
    for lex_id, lex_senses in sense_by_lex.items():
        distinct_domains = {s["domainKey"] for s in lex_senses}
        # Phải có ≥2 domain khác nhau, VÀ ít nhất 1 domain != general
        non_general = distinct_domains - {"general"}
        if len(distinct_domains) >= MIN_SENSES_FOR_POLYSEMY and non_general:
            polysemy_lexeme_ids.add(lex_id)

    # Apply filter
    lexemes = [l for l in lexemes if l["lexemeId"] in polysemy_lexeme_ids]
    senses  = [s for s in senses  if s["lexemeId"] in polysemy_lexeme_ids]

    print(f"  → After polysemy filter: {len(lexemes):,} Lexeme, {len(senses):,} Sense")

    print(f"\n── Kết quả ──")
    print(f"  Skipped (không có sense chuyên ngành): {skipped_no_specialized:,}")
    print(f"  Skipped (không có gloss):               {skipped_no_gloss:,}")
    print(f"  Lexeme giữ lại:  {len(lexemes):,}")
    print(f"  Sense giữ lại:   {len(senses):,}")

    # Stats per domain
    from collections import Counter
    domain_counts = Counter(s["domainKey"] for s in senses)
    print("\n  Phân bố theo domain:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"    {domain:12s}: {count:,} senses")

    # Save
    lex_path   = out_dir / "lexemes_raw.json"
    sense_path = out_dir / "senses_raw.json"

    with open(lex_path, "w", encoding="utf-8") as f:
        json.dump(lexemes, f, ensure_ascii=False, indent=2)
    with open(sense_path, "w", encoding="utf-8") as f:
        json.dump(senses, f, ensure_ascii=False, indent=2)

    print(f"\n  Saved: {lex_path}")
    print(f"  Saved: {sense_path}")

    return lexemes, senses


if __name__ == "__main__":
    lexemes, senses = extract_lexemes_and_senses()
