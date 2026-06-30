"""
parse_jmdict.py — Parse jmdict-simplified JSON → dictionary_entries (word type).
Kết hợp với JLPT level data từ open-anki-jlpt-decks CSV.

JMdict Simplified JSON (v3.6.x) không chứa JLPT level trực tiếp.
→ Dùng bổ sung từ CSV: https://github.com/jamsinclair/open-anki-jlpt-decks

JLPT CSV format (expression,reading,meaning,tags,guid):
  会う,あう,"to meet",JLPT JLPT_5 JLPT_N5,...

Strategy:
  1. Load JLPT CSVs → build {expression: level} lookup
  2. Parse JMdict JSON
  3. Match từng entry với lookup table bằng expression text
"""
import json
import uuid
import csv
import io
import requests
from pathlib import Path

# URL các file CSV JLPT
JLPT_CSV_URLS = {
    "N5": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n5.csv",
    "N4": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n4.csv",
    "N3": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n3.csv",
}

JLPT_CSV_LOCAL = {
    "N5": "data/raw/jlpt_n5.csv",
    "N4": "data/raw/jlpt_n4.csv",
    "N3": "data/raw/jlpt_n3.csv",
}


def download_jlpt_csvs(data_dir: str = "data/raw") -> None:
    """Tải JLPT CSV files nếu chưa có."""
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    for level, url in JLPT_CSV_URLS.items():
        local_path = f"{data_dir}/jlpt_{level.lower()}.csv"
        if Path(local_path).exists():
            print(f"  ✅ JLPT {level} CSV đã tồn tại")
            continue
        print(f"  Tải JLPT {level} CSV từ {url}...")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(local_path, "w", encoding="utf-8", newline="") as f:
            f.write(resp.text)
        print(f"  ✅ JLPT {level} saved to {local_path}")


def load_jlpt_lookup(data_dir: str = "data/raw") -> dict[str, str]:
    """
    Load JLPT CSV files và build lookup dict {expression: jlpt_level}.
    Ưu tiên level cao hơn nếu expression xuất hiện nhiều lần.
    """
    lookup: dict[str, str] = {}
    priority = {"N5": 1, "N4": 2, "N3": 3}  # N3 > N4 > N5

    for level in ["N5", "N4", "N3"]:
        csv_path = f"{data_dir}/jlpt_{level.lower()}.csv"
        if not Path(csv_path).exists():
            print(f"  WARNING: {csv_path} không tồn tại, skip.")
            continue

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                expr = row.get("expression", "").strip()
                if not expr:
                    continue
                # Nếu đã có, chỉ update nếu level này cao hơn
                existing = lookup.get(expr)
                if existing is None or priority[level] > priority.get(existing, 0):
                    lookup[expr] = level
                    count += 1
        print(f"  JLPT {level}: {count} expressions loaded")

    return lookup


def _extract_meaning_en(word: dict) -> str:
    """Lấy nghĩa tiếng Anh (tối đa 3 gloss từ sense đầu tiên)."""
    for sense in word.get("sense", []):
        glosses = [
            g["text"]
            for g in sense.get("gloss", [])
            if g.get("lang") == "eng"
        ]
        if glosses:
            return "; ".join(glosses[:3])
    return ""


def parse_jmdict(
    jmdict_path: str,
    jlpt_lookup: dict[str, str] = None,
    jlpt_csv_dir: str = "data/raw",
) -> list[dict]:
    """
    Parse jmdict-simplified JSON và trả về list[dict] các word entries JLPT N3-N5.

    Args:
        jmdict_path: Đường dẫn đến file jmdict-eng.json
        jlpt_lookup: Dict {expression: level} — nếu None sẽ tự load
        jlpt_csv_dir: Thư mục chứa JLPT CSV files

    Returns:
        list[dict] với các field:
          - id (uuid str)
          - entry_type = "word"
          - text (kanji form hoặc kana form)
          - reading (kana form)
          - meaning_en
          - meaning_vn (= meaning_en ban đầu, sẽ dịch sau)
          - jlpt_level ("N3" | "N4" | "N5")
          - explanation_short (None)
          - jmdict_id (id gốc để track)
    """
    # Load JLPT lookup nếu chưa có
    if jlpt_lookup is None:
        print("Loading JLPT level data...")
        download_jlpt_csvs(jlpt_csv_dir)
        jlpt_lookup = load_jlpt_lookup(jlpt_csv_dir)
        print(f"Total JLPT vocabulary: {len(jlpt_lookup):,} entries")

    print(f"\nLoading JMdict JSON from {jmdict_path}...")
    with open(jmdict_path, encoding="utf-8") as f:
        data = json.load(f)

    words = data.get("words", [])
    print(f"Total words in JMdict: {len(words):,}")

    entries = []
    skipped_no_jlpt = 0
    skipped_no_meaning = 0

    for word in words:
        # ── Text (dùng để tra JLPT) ─────────────────────────────
        kanji_forms = word.get("kanji", [])
        kana_forms = word.get("kana", [])
        text = kanji_forms[0]["text"] if kanji_forms else kana_forms[0]["text"]
        reading = kana_forms[0]["text"] if kana_forms else None

        # ── JLPT Level ────────────────────────────────────────────
        # Thử nhiều dạng text để tra lookup:
        #   1. Kanji form (VD: 食べる)
        #   2. Kana form (VD: たべる)
        jlpt_level = jlpt_lookup.get(text)
        if jlpt_level is None and reading and reading != text:
            jlpt_level = jlpt_lookup.get(reading)

        # Thử tất cả kanji forms
        if jlpt_level is None:
            for form in kanji_forms:
                jlpt_level = jlpt_lookup.get(form["text"])
                if jlpt_level:
                    break

        if jlpt_level is None:
            skipped_no_jlpt += 1
            continue

        # ── Meaning ───────────────────────────────────────────────
        meaning_en = _extract_meaning_en(word)
        if not meaning_en:
            skipped_no_meaning += 1
            continue

        # Nếu text == reading thì không cần reading riêng
        if text == reading:
            reading = None

        entries.append({
            "id": str(uuid.uuid4()),
            "entry_type": "word",
            "text": text,
            "reading": reading,
            "meaning_en": meaning_en,
            "meaning_vn": meaning_en,  # Placeholder, sẽ dịch ở bước 3
            "jlpt_level": jlpt_level,
            "explanation_short": None,
            "jmdict_id": word.get("id"),  # Track original ID
        })

    print(f"\nResults:")
    print(f"  Skipped (no JLPT N3-N5): {skipped_no_jlpt:,}")
    print(f"  Skipped (no meaning):    {skipped_no_meaning:,}")
    print(f"  Found: {len(entries):,} word entries (JLPT N3/N4/N5)")

    # Breakdown theo level
    from collections import Counter
    level_count = Counter(e["jlpt_level"] for e in entries)
    for level in ["N5", "N4", "N3"]:
        print(f"    {level}: {level_count.get(level, 0):,}")

    return entries


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/jmdict-eng.json"
    entries = parse_jmdict(path, jlpt_csv_dir="data/raw")
    print(f"\nSample entry: {entries[0] if entries else 'none'}")
