"""
main.py — Runner tổng hợp toàn bộ Dictionary Data Pipeline.

Chạy theo thứ tự:
  1. Parse JMdict → word entries (JLPT N3/N4/N5) với JLPT data từ CSV
  2. Parse Kanjidic2 → kanji entries (JLPT N3/N4/N5)
  3. Translate meanings EN → VI (deep-translator với cache)
  4. Build entry_relations (kanji, radical, compound, synonym)
  5. Load Tatoeba → examples
  6. Insert tất cả vào PostgreSQL

Usage:
  cd ai/scripts/seed_dictionary
  python main.py

  # Bỏ qua bước dịch (dùng nghĩa EN thay VI):
  python main.py --skip-translate

  # Bỏ qua bước examples (chạy nhanh hơn):
  python main.py --skip-examples

  # Chỉ verify DB (không insert gì):
  python main.py --verify-only

  # Chạy pipeline rút gọn (bỏ cả translate và examples):
  python main.py --skip-translate --skip-examples
"""
import argparse
import sys
import time
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data" / "raw"

JMDICT_PATH = DATA_DIR / "jmdict-eng.json"
KANJIDIC_PATH = DATA_DIR / "kanjidic2-en.json"
KRADFILE_PATH = DATA_DIR / "kradfile.json"
SENTENCES_PATH = DATA_DIR / "sentences.csv"
LINKS_PATH = DATA_DIR / "links.csv"
TRANSLATE_CACHE_PATH = SCRIPT_DIR / "data" / "translation_cache.json"


def check_data_files(skip_examples: bool = False) -> bool:
    """Kiểm tra các file raw data đã tồn tại chưa."""
    required = [JMDICT_PATH, KANJIDIC_PATH]
    if not skip_examples:
        required += [SENTENCES_PATH, LINKS_PATH]

    missing = [f for f in required if not f.exists()]
    if missing:
        print("❌ Thiếu các file raw data sau:")
        for f in missing:
            print(f"   {f}")
        print("\nVui lòng chạy trước: bash download_sources.sh")
        return False
    return True


def run_pipeline(
    skip_translate: bool = False,
    skip_examples: bool = False,
    verify_only: bool = False,
) -> None:
    start_time = time.time()

    print("=" * 60)
    print("  Dictionary Data Pipeline")
    print("=" * 60)

    # ── Verify only mode ─────────────────────────────────────────
    if verify_only:
        from load_to_postgres import verify_data
        verify_data()
        return

    # ── Check files ───────────────────────────────────────────────
    if not check_data_files(skip_examples):
        sys.exit(1)

    # ── Step 1: Parse JMdict ──────────────────────────────────────
    print("\n[1/6] Parsing JMdict (word entries) + JLPT data...")
    from parse_jmdict import parse_jmdict
    word_entries = parse_jmdict(
        jmdict_path=str(JMDICT_PATH),
        jlpt_csv_dir=str(DATA_DIR),
    )

    if not word_entries:
        print("❌ Không có word entries nào. Kiểm tra lại JMdict file và JLPT CSVs.")
        sys.exit(1)

    # ── Step 2: Parse Kanjidic2 ───────────────────────────────────
    print("\n[2/6] Parsing Kanjidic2 (kanji entries)...")
    from parse_kanjidic import parse_kanjidic
    kanji_entries = parse_kanjidic(str(KANJIDIC_PATH))

    # ── Step 3: Translate meanings ────────────────────────────────
    if skip_translate:
        print("\n[3/6] Skipping translation (dùng nghĩa tiếng Anh).")
    else:
        print("\n[3/6] Translating meanings EN → VI...")
        print("      Lưu ý: Bước này có thể mất vài giờ.")
        print("      Cache sẽ được lưu để tránh dịch lại khi restart.")
        from translate_meanings import translate_entries
        TRANSLATE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        word_entries = translate_entries(word_entries, str(TRANSLATE_CACHE_PATH))
        kanji_entries = translate_entries(kanji_entries, str(TRANSLATE_CACHE_PATH))

    # ── Step 4: Build relations ───────────────────────────────────
    print("\n[4/6] Building entry_relations...")
    from build_relations import build_all_relations

    # KradFile
    kradfile_str = str(KRADFILE_PATH) if KRADFILE_PATH.exists() else ""
    if not kradfile_str:
        print("      WARNING: kradfile.json không tìm thấy, bỏ qua radical relations.")

    relations = build_all_relations(
        word_entries=word_entries,
        kanji_entries=kanji_entries,
        kradfile_path=kradfile_str,
        jmdict_path=str(JMDICT_PATH),
    )

    # ── Step 5: Import examples ───────────────────────────────────
    examples = []
    if skip_examples:
        print("\n[5/6] Skipping examples import.")
    else:
        print("\n[5/6] Loading Tatoeba examples...")
        from import_examples import load_tatoeba_pairs, match_examples_to_entries
        pairs = load_tatoeba_pairs(str(SENTENCES_PATH), str(LINKS_PATH))
        examples = match_examples_to_entries(pairs, word_entries, max_per_entry=3)

    # ── Step 6: Load to PostgreSQL ────────────────────────────────
    print("\n[6/6] Loading data to PostgreSQL...")
    from load_to_postgres import load_all, verify_data
    load_all(word_entries, kanji_entries, relations, examples)

    # ── Verification ─────────────────────────────────────────────
    print("\n[✓] Verification:")
    verify_data()

    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)
    print(f"\n{'=' * 60}")
    print(f"  Pipeline hoàn thành trong {minutes}m {seconds}s")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Dictionary Data Pipeline — Import từ điển Nhật vào PostgreSQL"
    )
    parser.add_argument(
        "--skip-translate",
        action="store_true",
        help="Bỏ qua bước dịch EN→VI (dùng nghĩa tiếng Anh)",
    )
    parser.add_argument(
        "--skip-examples",
        action="store_true",
        help="Bỏ qua bước import câu ví dụ Tatoeba (chạy nhanh hơn)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Chỉ kiểm tra dữ liệu trong DB, không insert gì",
    )

    args = parser.parse_args()
    run_pipeline(
        skip_translate=args.skip_translate,
        skip_examples=args.skip_examples,
        verify_only=args.verify_only,
    )


if __name__ == "__main__":
    main()
