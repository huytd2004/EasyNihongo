"""
parse_kanjidic.py — Parse Kanjidic2 JSON (từ jmdict-simplified) → dictionary_entries (kanji type).

Sử dụng kanjidic2-en.json (đã parse sẵn từ jmdict-simplified release).

Schema kanjidic2-en.json:
{
  "characters": [
    {
      "literal": "悪",
      "misc": {
        "grade": 3,
        "strokeCounts": [11],
        "frequency": 530,
        "jlptLevel": 3    <- int: 1=N1, 2=N2, 3=N3, 4=N4 (N5 không có tag)
      },
      "readingMeaning": {
        "groups": [
          {
            "readings": [
              {"type": "ja_on",  "value": "アク"},
              {"type": "ja_kun", "value": "わる.い"},
              ...
            ],
            "meanings": [
              {"lang": "en", "value": "bad"},
              ...
            ]
          }
        ]
      }
    }
  ]
}

JLPT mapping:
  jlptLevel 3 → N3
  jlptLevel 4 → N4
  jlptLevel null + grade <= 6 → N5 (tiểu học)
"""
import json
import uuid

# Kanjidic2 dùng int: 1=N1, 2=N2, 3=N3, 4=N4
JLPT_NUM_MAP = {3: "N3", 4: "N4"}
TARGET_LEVELS = {"N3", "N4", "N5"}


def parse_kanjidic(kanjidic_path: str) -> list[dict]:
    """
    Parse Kanjidic2 JSON và trả về list[dict] kanji entries JLPT N3/N4/N5.

    Args:
        kanjidic_path: Đường dẫn đến file kanjidic2-en.json

    Returns:
        list[dict] với các field:
          - id (uuid str)
          - entry_type = "kanji"
          - text (ký tự kanji)
          - reading (on+kun, format: "アク、わる.い")
          - meaning_en
          - meaning_vn (= meaning_en, dịch sau)
          - jlpt_level ("N3" | "N4" | "N5")
          - explanation_short (số nét + grade)
    """
    print(f"Parsing Kanjidic2 JSON from {kanjidic_path}...")
    with open(kanjidic_path, encoding="utf-8") as f:
        data = json.load(f)

    characters = data.get("characters", [])
    print(f"Total characters in Kanjidic2: {len(characters):,}")

    entries = []
    skipped = 0

    for char in characters:
        literal = char.get("literal", "")
        if not literal:
            continue

        misc = char.get("misc", {})

        # ── JLPT Level ──────────────────────────────────────────
        jlpt_num = misc.get("jlptLevel")
        jlpt_level = JLPT_NUM_MAP.get(jlpt_num)

        if jlpt_level is None:
            # Không có JLPT tag → xem grade (1-6 = tiểu học → N5)
            grade = misc.get("grade")
            if grade is not None and isinstance(grade, int) and grade <= 6:
                jlpt_level = "N5"

        if jlpt_level not in TARGET_LEVELS:
            skipped += 1
            continue

        # ── Reading ─────────────────────────────────────────────
        reading_meaning = char.get("readingMeaning")
        on_readings = []
        kun_readings = []
        meanings_en = []

        if reading_meaning:
            for group in reading_meaning.get("groups", []):
                for r in group.get("readings", []):
                    if r.get("type") == "ja_on" and r.get("value"):
                        on_readings.append(r["value"])
                    elif r.get("type") == "ja_kun" and r.get("value"):
                        kun_readings.append(r["value"])
                for m in group.get("meanings", []):
                    if m.get("lang") == "en" and m.get("value"):
                        meanings_en.append(m["value"])

        reading_parts = on_readings[:2] + kun_readings[:2]
        reading = "、".join(reading_parts) if reading_parts else None
        meaning_en = "; ".join(meanings_en[:3]) if meanings_en else ""

        if not meaning_en:
            skipped += 1
            continue

        # ── Extra info ───────────────────────────────────────────
        stroke_counts = misc.get("strokeCounts", [])
        stroke = stroke_counts[0] if stroke_counts else None
        grade = misc.get("grade")

        explanation_parts = []
        if stroke:
            explanation_parts.append(f"Số nét: {stroke}")
        if grade:
            explanation_parts.append(f"Lớp: {grade}")
        explanation_short = " | ".join(explanation_parts) if explanation_parts else None

        entries.append({
            "id": str(uuid.uuid4()),
            "entry_type": "kanji",
            "text": literal,
            "reading": reading,
            "meaning_en": meaning_en,
            "meaning_vn": meaning_en,  # Placeholder, dịch sau
            "jlpt_level": jlpt_level,
            "explanation_short": explanation_short,
        })

    print(f"Skipped (no JLPT N3-N5 or no meaning): {skipped:,}")
    print(f"Found {len(entries):,} kanji entries (JLPT N3/N4/N5)")

    # Breakdown theo level
    from collections import Counter
    level_count = Counter(e["jlpt_level"] for e in entries)
    for level in ["N5", "N4", "N3"]:
        print(f"  {level}: {level_count.get(level, 0):,}")

    return entries


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/kanjidic2-en.json"
    entries = parse_kanjidic(path)
    if entries:
        print(f"\nSample entry: {entries[0]}")
