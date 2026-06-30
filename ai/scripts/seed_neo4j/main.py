"""
main.py — Runner tổng hợp cho Neo4j seeding pipeline.

Thứ tự:
  1. extract_from_jmdict  → lexemes_raw.json, senses_raw.json
  2. build_cue_mapping    → cue_mapping_raw.json
  3. translate_vi         → senses_translated.json  (optional, --skip-translate)
  4. generate_csvs        → 4 CSV files
  5. load_to_neo4j        → Import vào Neo4j
  6. verify_neo4j         → Kiểm tra kết quả

Usage:
  python main.py                        # Full pipeline (có dịch)
  python main.py --skip-translate       # Bỏ bước dịch (dùng nghĩa EN)
  python main.py --csv-only             # Chỉ generate CSVs (skip Neo4j load)
  python main.py --load-only            # Chỉ load CSVs vào Neo4j (đã có CSV)
  python main.py --verify-only          # Chỉ verify Neo4j
  python main.py --jmdict /path/to/jmdict-eng.json  # Chỉ định path JMdict
"""
import argparse
import sys
import time
from pathlib import Path

from config import NEO4J_DIR, JMDICT_JSON


def parse_args():
    parser = argparse.ArgumentParser(
        description="Neo4j Knowledge Graph seeding pipeline"
    )
    parser.add_argument(
        "--skip-translate",
        action="store_true",
        help="Bỏ qua bước dịch EN→VI (dùng glossEn làm glossVi)",
    )
    parser.add_argument(
        "--use-corpus",
        action="store_true",
        default=True,
        help="Dùng Tatoeba corpus để build sense-specific cues (mặc định: True)",
    )
    parser.add_argument(
        "--no-corpus",
        action="store_true",
        help="Dùng domain seed cues thay vì corpus (nhanh hơn, ít chính xác hơn)",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Chỉ generate CSV files, không load vào Neo4j",
    )
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="Chỉ load CSV files vào Neo4j (đã có CSV sẵn)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Chỉ chạy verification queries",
    )
    parser.add_argument(
        "--jmdict",
        type=str,
        default=None,
        help="Đường dẫn đến jmdict-eng.json (mặc định: tự tìm từ seed_dictionary/data/raw/)",
    )
    return parser.parse_args()


def banner(text: str) -> None:
    width = 60
    print(f"\n{'─' * width}")
    print(f"  {text}")
    print(f"{'─' * width}")


def step_extract(jmdict_path: Path | None) -> None:
    banner("STEP 1: Extract Lexeme & Sense từ JMdict")
    from extract_from_jmdict import extract_lexemes_and_senses
    path = jmdict_path or JMDICT_JSON
    extract_lexemes_and_senses(jmdict_path=path, out_dir=NEO4J_DIR)


def step_cue() -> None:
    banner("STEP 2: Build Cue Mapping (rule-based domain seeds)")
    from build_cue_mapping import build_cue_mapping
    build_cue_mapping(out_dir=NEO4J_DIR)


def step_cue_corpus() -> None:
    banner("STEP 2: Build Cue Mapping (corpus-derived từ Tatoeba)")
    from build_cue_from_corpus import build_cue_from_corpus
    build_cue_from_corpus(out_dir=NEO4J_DIR)


def step_translate() -> None:
    banner("STEP 3: Translate EN → VI")
    from translate_vi import translate_senses
    translate_senses(out_dir=NEO4J_DIR)


def step_csvs() -> None:
    banner("STEP 4: Generate CSV files")
    from generate_csvs import generate_csvs
    generate_csvs(out_dir=NEO4J_DIR)


def step_load() -> None:
    banner("STEP 5: Load CSV → Neo4j")
    from load_to_neo4j import load_to_neo4j
    load_to_neo4j(data_dir=NEO4J_DIR)


def step_verify() -> None:
    banner("STEP 6: Verify Neo4j Graph")
    from verify_neo4j import main as verify_main
    verify_main()


def main():
    args = parse_args()
    start = time.time()

    # ── Chế độ đặc biệt ──────────────────────────────────────────────────────

    if args.verify_only:
        step_verify()
        return

    if args.load_only:
        step_load()
        step_verify()
        return

    # ── Full pipeline ─────────────────────────────────────────────────────────

    jmdict_path = Path(args.jmdict) if args.jmdict else None
    use_corpus = not args.no_corpus  # Default: True

    # Step 1: Extract
    step_extract(jmdict_path)

    # Step 2: Cue mapping
    if use_corpus:
        step_cue_corpus()   # Corpus-derived (khuyến nghị)
    else:
        step_cue()          # Rule-based domain seeds (nhanh hơn)

    # Step 3: Translate (optional)
    if not args.skip_translate:
        step_translate()
    else:
        print("\n[SKIP] Bước dịch bị bỏ qua (--skip-translate)")
        print("  glossVi sẽ = glossEn trong CSV.")

    # Step 4: Generate CSVs
    step_csvs()

    # Step 5: Load to Neo4j (nếu không phải --csv-only)
    if not args.csv_only:
        step_load()
        step_verify()
    else:
        print("\n[SKIP] Bỏ qua load to Neo4j (--csv-only)")
        print(f"  CSV files đã sẵn sàng tại: {NEO4J_DIR}")

    elapsed = time.time() - start
    mins, secs = divmod(int(elapsed), 60)
    print(f"\n🎉 Pipeline hoàn tất trong {mins}m {secs}s")


if __name__ == "__main__":
    main()
