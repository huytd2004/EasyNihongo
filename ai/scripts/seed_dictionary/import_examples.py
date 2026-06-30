"""
import_examples.py — Import câu ví dụ từ Tatoeba corpus.

Tatoeba export format:
  sentences.csv:   id\tlang\ttext  (tab-separated, no header)
  links.csv:       sentence_id\ttranslation_id  (tab-separated, no header)

Strategy:
  1. Load JA sentences, VI sentences
  2. Find JA↔VI links (direct translation pairs)
  3. Match sentences với dictionary entries (từ xuất hiện trong câu)
  4. Tối đa max_per_entry câu/từ để tránh data lệch
"""
import uuid
import pandas as pd
from pathlib import Path
from tqdm import tqdm


def load_tatoeba_pairs(
    sentences_path: str,
    links_path: str,
) -> pd.DataFrame:
    """
    Load Tatoeba sentences và links, trả về DataFrame các cặp JA-VI.

    Args:
        sentences_path: Đường dẫn sentences.csv
        links_path: Đường dẫn links.csv

    Returns:
        DataFrame với columns: ["japanese", "vietnamese"]
    """
    print(f"Loading Tatoeba sentences from {sentences_path}...")

    # sentences.csv: id, lang, text (tab-separated, ~9M rows)
    sentences = pd.read_csv(
        sentences_path,
        sep="\t",
        names=["id", "lang", "text"],
        dtype={"id": "int64", "lang": str, "text": str},
        low_memory=False,
        on_bad_lines="skip",
    )

    print(f"Total sentences loaded: {len(sentences):,}")

    # Tách JA và VI
    ja_mask = sentences["lang"] == "jpn"
    vi_mask = sentences["lang"] == "vie"

    ja_sents = sentences[ja_mask].set_index("id")["text"]
    vi_sents = sentences[vi_mask].set_index("id")["text"]

    print(f"  Japanese: {len(ja_sents):,} sentences")
    print(f"  Vietnamese: {len(vi_sents):,} sentences")

    # Load links
    print(f"Loading Tatoeba links from {links_path}...")
    links = pd.read_csv(
        links_path,
        sep="\t",
        names=["src_id", "tgt_id"],
        dtype={"src_id": "int64", "tgt_id": "int64"},
    )
    print(f"Total links: {len(links):,}")

    # Lọc chỉ cặp JA→VI
    ja_ids = set(ja_sents.index)
    vi_ids = set(vi_sents.index)

    ja_vi_mask = links["src_id"].isin(ja_ids) & links["tgt_id"].isin(vi_ids)
    vi_ja_mask = links["src_id"].isin(vi_ids) & links["tgt_id"].isin(ja_ids)

    ja_vi_links = links[ja_vi_mask].copy()
    vi_ja_links = links[vi_ja_mask].copy()

    # Normalize vi_ja → ja_vi
    vi_ja_links = vi_ja_links.rename(columns={"src_id": "tgt_id", "tgt_id": "src_id"})

    all_links = pd.concat([ja_vi_links, vi_ja_links]).drop_duplicates()

    # Map sentences
    all_links["japanese"] = all_links["src_id"].map(ja_sents)
    all_links["vietnamese"] = all_links["tgt_id"].map(vi_sents)

    pairs = all_links[["japanese", "vietnamese"]].dropna()
    print(f"Found {len(pairs):,} JA–VI sentence pairs")

    return pairs.reset_index(drop=True)


def match_examples_to_entries(
    pairs: pd.DataFrame,
    word_entries: list[dict],
    max_per_entry: int = 3,
) -> list[dict]:
    """
    Ghép câu ví dụ với dictionary entries.
    Chỉ lấy câu có chứa từ (exact substring match).

    Args:
        pairs: DataFrame với columns ["japanese", "vietnamese"]
        word_entries: list[dict] word entries (chỉ word, không phải kanji)
        max_per_entry: Tối đa bao nhiêu câu mỗi từ

    Returns:
        list[dict] examples với fields: id, entry_id, japanese_sentence, vietnamese_sentence
    """
    print(f"\nMatching examples for {len(word_entries):,} word entries...")
    print(f"Available sentence pairs: {len(pairs):,}")

    # Pre-build a quick lookup: Japanese text → row indices
    # Dùng pandas str.contains cho tốc độ
    examples = []
    no_match_count = 0

    for entry in tqdm(word_entries, desc="Matching examples"):
        word_text = entry["text"]
        if not word_text:
            continue

        # Filter câu chứa từ này (exact substring, không regex)
        try:
            mask = pairs["japanese"].str.contains(word_text, regex=False, na=False)
            matched = pairs[mask].head(max_per_entry)
        except Exception:
            continue

        if matched.empty:
            no_match_count += 1
            continue

        for _, row in matched.iterrows():
            examples.append({
                "id": str(uuid.uuid4()),
                "entry_id": entry["id"],
                "japanese_sentence": row["japanese"],
                "vietnamese_sentence": row["vietnamese"],
            })

    print(f"Matched {len(examples):,} examples")
    print(f"  Words without examples: {no_match_count:,}")

    return examples


if __name__ == "__main__":
    import sys
    sentences_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/sentences.csv"
    links_path = sys.argv[2] if len(sys.argv) > 2 else "data/raw/links.csv"

    pairs = load_tatoeba_pairs(sentences_path, links_path)
    print(f"\nSample pairs:")
    print(pairs.head(5).to_string())
