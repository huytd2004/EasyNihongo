"""
build_relations.py — Xây dựng tất cả 4 loại entry_relations.

Relation types:
  1. "kanji"    — Word chứa Kanji component (勉強 → 勉, 強)
  2. "radical"  — Kanji chứa radical/bộ thủ (漢 → 氵, 廿, 口, 夫) [KradFile]
  3. "compound" — Các từ dùng chung một kanji (強化, 強調, 強制 cùng dùng 強)
  4. "synonym"  — Từ đồng nghĩa [JMdict related field]
"""
import uuid
import json
from collections import defaultdict


def is_kanji(char: str) -> bool:
    """Kiểm tra ký tự có phải CJK Unified Ideographs không."""
    return "\u4e00" <= char <= "\u9fff"


# ─────────────────────────────────────────────────────────────────────────────
# 1. relation_type = "kanji"
#    Word (勉強) → các Kanji thành phần (勉, 強)
#    Nguồn: tính toán từ text của word entries
# ─────────────────────────────────────────────────────────────────────────────

def build_kanji_relations(
    word_entries: list[dict],
    kanji_index: dict,  # {kanji_text: entry_id}
) -> list[dict]:
    """
    Với mỗi word, tìm các kanji trong text và tạo relation.

    Args:
        word_entries: list[dict] word entries
        kanji_index: dict mapping kanji character → entry id

    Returns:
        list[dict] relations với relation_type="kanji"
    """
    relations = []
    for word in word_entries:
        text = word.get("text", "")
        for order, char in enumerate(text):
            if is_kanji(char) and char in kanji_index:
                relations.append({
                    "id": str(uuid.uuid4()),
                    "source_id": word["id"],
                    "target_id": kanji_index[char],
                    "relation_type": "kanji",
                    "order_index": order,
                })
    print(f"[kanji] Built {len(relations):,} relations")
    return relations


# ─────────────────────────────────────────────────────────────────────────────
# 2. relation_type = "radical"
#    Kanji → bộ thủ cấu thành
#    Nguồn: kradfile.json (từ jmdict-simplified, format JSON)
#    Format JSON: {"kanji": {"亜": ["｜", "一", "口"], ...}}
# ─────────────────────────────────────────────────────────────────────────────

def build_radical_relations(
    kradfile_path: str,
    kanji_index: dict,  # {kanji_text: entry_id}
) -> list[dict]:
    """
    Đọc kradfile.json (jmdict-simplified format) và tạo kanji → radical relations.
    Chỉ tạo relation nếu cả source lẫn target đều có trong kanji_index.

    Args:
        kradfile_path: Đường dẫn kradfile.json
        kanji_index: dict mapping kanji char → entry id

    Returns:
        list[dict] relations với relation_type="radical"
    """
    relations = []

    if not kradfile_path:
        print("[radical] WARNING: KradFile path rỗng, bỏ qua.")
        return relations

    try:
        with open(kradfile_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[radical] WARNING: KradFile không tìm thấy tại {kradfile_path}, bỏ qua.")
        return relations

    # kradfile.json format: {"kanji": {"亜": ["｜", "一", "口"], ...}}
    kanji_map = data.get("kanji", {})
    if not kanji_map:
        print("[radical] WARNING: kradfile.json không có 'kanji' key.")
        return relations

    for kanji_char, radicals in kanji_map.items():
        if kanji_char not in kanji_index:
            continue  # Kanji này không có trong DB của chúng ta

        source_id = kanji_index[kanji_char]
        for order, radical in enumerate(radicals):
            if radical in kanji_index:  # Radical cũng phải là entry trong DB
                relations.append({
                    "id": str(uuid.uuid4()),
                    "source_id": source_id,
                    "target_id": kanji_index[radical],
                    "relation_type": "radical",
                    "order_index": order,
                })

    print(f"[radical] Built {len(relations):,} relations")
    return relations


# ─────────────────────────────────────────────────────────────────────────────
# 3. relation_type = "compound"
#    Các word dùng chung một kanji → link compound
#    VD: 強化, 強調, 強制 đều có 強 → link compound với nhau
#    Nguồn: tính toán từ word_entries (không cần nguồn ngoài)
# ─────────────────────────────────────────────────────────────────────────────

def build_compound_relations(
    word_entries: list[dict],
    max_compounds_per_kanji: int = 5,
) -> list[dict]:
    """
    Nhóm word entries theo kanji chứa trong text.
    Với mỗi nhóm (>= 2 words), tạo compound relations giữa chúng.

    Args:
        word_entries: list[dict] word entries
        max_compounds_per_kanji: Giới hạn số cặp mỗi kanji để tránh explosion

    Returns:
        list[dict] relations với relation_type="compound"
    """
    # Group words by kanji
    kanji_to_words: dict[str, list[dict]] = defaultdict(list)
    for word in word_entries:
        text = word.get("text", "")
        seen_kanji = set()
        for char in text:
            if is_kanji(char) and char not in seen_kanji:
                kanji_to_words[char].append(word)
                seen_kanji.add(char)

    relations = []
    seen_pairs: set[tuple] = set()  # Tránh duplicate A→B và B→A

    for kanji_char, words in kanji_to_words.items():
        if len(words) < 2:
            continue

        count = 0
        for i, w1 in enumerate(words):
            if count >= max_compounds_per_kanji:
                break
            for w2 in words[i + 1:]:
                if count >= max_compounds_per_kanji:
                    break
                # Tránh duplicate (sort để không phân biệt thứ tự)
                pair = (min(w1["id"], w2["id"]), max(w1["id"], w2["id"]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                relations.append({
                    "id": str(uuid.uuid4()),
                    "source_id": w1["id"],
                    "target_id": w2["id"],
                    "relation_type": "compound",
                    "order_index": None,
                })
                count += 1

    print(f"[compound] Built {len(relations):,} relations")
    return relations


# ─────────────────────────────────────────────────────────────────────────────
# 4. relation_type = "synonym"
#    Từ đồng nghĩa: trích xuất từ JMdict "related" field
#    Nguồn: jmdict-simplified JSON
# ─────────────────────────────────────────────────────────────────────────────

def build_synonym_relations(
    jmdict_path: str,
    word_index: dict,  # {word_text: entry_id}
) -> list[dict]:
    """
    Đọc jmdict-simplified JSON và tạo synonym relations từ sense.related field.

    Args:
        jmdict_path: Đường dẫn đến jmdict-examples-all.json
        word_index: dict mapping word text → entry id

    Returns:
        list[dict] relations với relation_type="synonym"
    """
    print(f"Loading JMdict for synonym extraction...")

    try:
        with open(jmdict_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[synonym] WARNING: JMdict không tìm thấy, bỏ qua synonym.")
        return []

    relations = []
    seen_pairs: set[tuple] = set()

    for word in data.get("words", []):
        # Source text
        kanji_forms = word.get("kanji", [])
        kana_forms = word.get("kana", [])
        source_text = kanji_forms[0]["text"] if kanji_forms else kana_forms[0]["text"]

        if source_text not in word_index:
            continue

        source_id = word_index[source_text]

        for sense in word.get("sense", []):
            # jmdict-simplified: field "related" là list of xref
            # Mỗi xref có thể là: ["食べ物", 1] hoặc ["たべもの"]
            for related in sense.get("related", []):
                if isinstance(related, list) and related:
                    target_text = related[0]
                elif isinstance(related, str):
                    target_text = related
                else:
                    continue

                if target_text not in word_index or target_text == source_text:
                    continue

                target_id = word_index[target_text]
                pair = (min(source_id, target_id), max(source_id, target_id))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                relations.append({
                    "id": str(uuid.uuid4()),
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": "synonym",
                    "order_index": None,
                })

    print(f"[synonym] Built {len(relations):,} relations from JMdict")
    return relations


# ─────────────────────────────────────────────────────────────────────────────
# Runner tổng hợp
# ─────────────────────────────────────────────────────────────────────────────

def build_all_relations(
    word_entries: list[dict],
    kanji_entries: list[dict],
    kradfile_path: str,
    jmdict_path: str,
) -> list[dict]:
    """
    Xây dựng tất cả 4 loại relations.

    Args:
        word_entries: list[dict] word entries
        kanji_entries: list[dict] kanji entries
        kradfile_path: Đường dẫn KradFile
        jmdict_path: Đường dẫn JMdict JSON

    Returns:
        list[dict] tất cả relations
    """
    # Build indexes
    kanji_index = {e["text"]: e["id"] for e in kanji_entries}
    word_index = {e["text"]: e["id"] for e in word_entries}

    print("\n=== Building entry_relations ===")

    relations = []
    relations += build_kanji_relations(word_entries, kanji_index)
    relations += build_radical_relations(kradfile_path, kanji_index)
    relations += build_compound_relations(word_entries)
    relations += build_synonym_relations(jmdict_path, word_index)

    print(f"\nTotal relations: {len(relations):,}")

    # Breakdown theo type
    from collections import Counter
    type_count = Counter(r["relation_type"] for r in relations)
    for rel_type, count in sorted(type_count.items()):
        print(f"  {rel_type}: {count:,}")

    return relations


if __name__ == "__main__":
    print("Test build_kanji_relations:")
    test_words = [
        {"id": "w1", "text": "勉強", "entry_type": "word"},
        {"id": "w2", "text": "食べ物", "entry_type": "word"},
    ]
    test_kanjis = [
        {"id": "k1", "text": "勉", "entry_type": "kanji"},
        {"id": "k2", "text": "強", "entry_type": "kanji"},
        {"id": "k3", "text": "食", "entry_type": "kanji"},
        {"id": "k4", "text": "物", "entry_type": "kanji"},
    ]
    kanji_idx = {k["text"]: k["id"] for k in test_kanjis}
    rels = build_kanji_relations(test_words, kanji_idx)
    for r in rels:
        src = next(w["text"] for w in test_words if w["id"] == r["source_id"])
        tgt = next(k["text"] for k in test_kanjis if k["id"] == r["target_id"])
        print(f"  {src} → {tgt} (order={r['order_index']})")
