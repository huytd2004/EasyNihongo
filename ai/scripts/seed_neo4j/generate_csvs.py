"""
generate_csvs.py — Tổng hợp JSON data → 4 CSV files chuẩn cho Neo4j LOAD CSV.

Output (trong data/neo4j/):
  domains.csv          — domainId, name
  lexemes.csv          — lexemeId, surface, reading, pos, jlpt
  senses.csv           — senseId, glossVi, domain, lexemeId
  sense_cue_mapping.csv — senseId, cueSurface
"""
import csv
import json
from pathlib import Path

from config import NEO4J_DIR, DOMAINS


def generate_csvs(out_dir: Path = NEO4J_DIR) -> None:
    """
    Đọc các file JSON intermediate và xuất ra 4 CSV files.
    Nếu senses_translated.json tồn tại, dùng nó; nếu không dùng senses_raw.json.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load lexemes
    lex_path = out_dir / "lexemes_raw.json"
    if not lex_path.exists():
        raise FileNotFoundError("Không tìm thấy lexemes_raw.json. Chạy extract_from_jmdict.py trước.")
    with open(lex_path, encoding="utf-8") as f:
        lexemes: list[dict] = json.load(f)

    # Load senses (prefer translated)
    sense_translated = out_dir / "senses_translated.json"
    sense_raw        = out_dir / "senses_raw.json"
    if sense_translated.exists():
        print(f"Using translated senses: {sense_translated}")
        with open(sense_translated, encoding="utf-8") as f:
            senses: list[dict] = json.load(f)
    elif sense_raw.exists():
        print(f"WARNING: Dùng senses_raw.json (chưa dịch). Nên chạy translate_vi.py trước.")
        with open(sense_raw, encoding="utf-8") as f:
            senses = json.load(f)
        # glossVi = glossEn nếu chưa dịch
        for s in senses:
            if not s.get("glossVi"):
                s["glossVi"] = s.get("glossEn", "")
    else:
        raise FileNotFoundError("Không tìm thấy senses file. Chạy extract_from_jmdict.py trước.")

    # Load cue mapping
    cue_path = out_dir / "cue_mapping_raw.json"
    if not cue_path.exists():
        raise FileNotFoundError("Không tìm thấy cue_mapping_raw.json. Chạy build_cue_mapping.py trước.")
    with open(cue_path, encoding="utf-8") as f:
        cue_mapping: list[dict] = json.load(f)

    # ── 1. domains.csv ────────────────────────────────────────────────────────
    domains_path = out_dir / "domains.csv"
    with open(domains_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["domainId", "name"])
        for domain_key, domain_label in DOMAINS.items():
            writer.writerow([f"domain_{domain_key}", domain_key])
    print(f"✅ domains.csv      — {len(DOMAINS)} rows")

    # ── 2. lexemes.csv ────────────────────────────────────────────────────────
    lexemes_path = out_dir / "lexemes.csv"
    with open(lexemes_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["lexemeId", "surface", "reading", "pos", "jlpt"])
        for lex in lexemes:
            writer.writerow([
                lex["lexemeId"],
                lex["surface"],
                lex.get("reading", ""),
                lex.get("pos", "n"),
                lex.get("jlpt", ""),
            ])
    print(f"✅ lexemes.csv      — {len(lexemes):,} rows")

    # ── 3. senses.csv ────────────────────────────────────────────────────────
    senses_path = out_dir / "senses.csv"
    with open(senses_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["senseId", "glossVi", "domain", "lexemeId"])
        skipped = 0
        written = 0
        for sense in senses:
            gloss_vi = sense.get("glossVi") or sense.get("glossEn", "")
            if not gloss_vi:
                skipped += 1
                continue
            writer.writerow([
                sense["senseId"],
                gloss_vi,
                sense["domain"],      # e.g. "domain_technology"
                sense["lexemeId"],
            ])
            written += 1
    print(f"✅ senses.csv       — {written:,} rows ({skipped} skipped, no gloss)")

    # ── 4. sense_cue_mapping.csv ──────────────────────────────────────────────
    cue_csv_path = out_dir / "sense_cue_mapping.csv"
    # Lấy set senseId hợp lệ (có trong senses.csv)
    valid_sense_ids: set[str] = {s["senseId"] for s in senses}
    with open(cue_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["senseId", "cueSurface"])
        written_cue = 0
        skipped_cue = 0
        for cue in cue_mapping:
            if cue["senseId"] not in valid_sense_ids:
                skipped_cue += 1
                continue
            writer.writerow([cue["senseId"], cue["cueSurface"]])
            written_cue += 1
    print(f"✅ sense_cue_mapping.csv — {written_cue:,} rows ({skipped_cue} skipped)")

    print(f"\n📁 All CSVs saved to: {out_dir}")
    print("\nNext step: python load_to_neo4j.py")


if __name__ == "__main__":
    generate_csvs()
