"""
load_to_postgres.py — Insert tất cả dictionary data vào PostgreSQL.

Sử dụng psycopg2 với execute_batch cho hiệu suất cao.
Connection string đọc từ biến môi trường DATABASE_URL hoặc hardcode fallback.

Tables:
  1. dictionary_entries  (word + kanji entries)
  2. entry_relations     (kanji, radical, compound, synonym)
  3. examples            (Tatoeba JA–VI sentences)
"""
import os
import psycopg2
import psycopg2.extras
from pathlib import Path


def get_db_connection():
    """
    Lấy connection PostgreSQL.
    Ưu tiên: DATABASE_URL env → fallback application.yaml config.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback: dùng config từ application.yaml
        db_url = "postgresql://postgres:123456@localhost:5432/datn"
        print(f"Sử dụng fallback DATABASE_URL: {db_url}")
    else:
        print(f"Sử dụng DATABASE_URL từ env")

    return psycopg2.connect(db_url)


def load_dictionary_entries(
    cur,
    entries: list[dict],
    batch_size: int = 500,
) -> None:
    """
    INSERT vào bảng dictionary_entries.
    Dùng ON CONFLICT DO NOTHING để idempotent (có thể chạy lại).
    """
    print(f"  Inserting {len(entries):,} dictionary entries...")

    # Chuẩn bị data (chỉ lấy các field cần thiết)
    rows = [
        {
            "id": e["id"],
            "entry_type": e["entry_type"],
            "text": e["text"],
            "reading": e.get("reading"),
            "meaning_vn": e.get("meaning_vn") or e.get("meaning_en", ""),
            "jlpt_level": e.get("jlpt_level"),
            "explanation_short": e.get("explanation_short"),
        }
        for e in entries
    ]

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO dictionary_entries
            (id, entry_type, text, reading, meaning_vn, jlpt_level, explanation_short)
        VALUES
            (%(id)s, %(entry_type)s, %(text)s, %(reading)s, %(meaning_vn)s,
             %(jlpt_level)s, %(explanation_short)s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
        page_size=batch_size,
    )
    print(f"  ✅ dictionary_entries done.")


def load_entry_relations(
    cur,
    relations: list[dict],
    batch_size: int = 500,
) -> None:
    """INSERT vào bảng entry_relations."""
    print(f"  Inserting {len(relations):,} entry relations...")

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO entry_relations
            (id, source_id, target_id, relation_type, order_index)
        VALUES
            (%(id)s, %(source_id)s, %(target_id)s, %(relation_type)s, %(order_index)s)
        ON CONFLICT (id) DO NOTHING
        """,
        relations,
        page_size=batch_size,
    )
    print(f"  ✅ entry_relations done.")


def load_examples(
    cur,
    examples: list[dict],
    batch_size: int = 500,
) -> None:
    """INSERT vào bảng examples."""
    print(f"  Inserting {len(examples):,} examples...")

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO examples
            (id, entry_id, japanese_sentence, vietnamese_sentence)
        VALUES
            (%(id)s, %(entry_id)s, %(japanese_sentence)s, %(vietnamese_sentence)s)
        ON CONFLICT (id) DO NOTHING
        """,
        examples,
        page_size=batch_size,
    )
    print(f"  ✅ examples done.")


def load_all(
    word_entries: list[dict],
    kanji_entries: list[dict],
    relations: list[dict],
    examples: list[dict],
) -> None:
    """
    Load tất cả data vào PostgreSQL theo thứ tự:
    dictionary_entries → entry_relations → examples

    Args:
        word_entries: list[dict] word entries
        kanji_entries: list[dict] kanji entries
        relations: list[dict] entry_relations
        examples: list[dict] examples
    """
    print("\n=== Loading data vào PostgreSQL ===")

    all_entries = word_entries + kanji_entries
    print(f"Total entries: {len(all_entries):,} ({len(word_entries):,} words + {len(kanji_entries):,} kanji)")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. dictionary_entries (phải insert trước vì relations + examples FK)
        load_dictionary_entries(cur, all_entries)

        # 2. entry_relations
        if relations:
            load_entry_relations(cur, relations)
        else:
            print("  ⚠️  Không có relations để insert.")

        # 3. examples
        if examples:
            load_examples(cur, examples)
        else:
            print("  ⚠️  Không có examples để insert.")

        conn.commit()
        print("\n✅ Commit thành công!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi, đã rollback: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_data() -> None:
    """
    Query PostgreSQL để verify số lượng records.
    Chạy sau khi load xong để kiểm tra.
    """
    print("\n=== Verification ===")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # dictionary_entries by type & level
        cur.execute("""
            SELECT entry_type, jlpt_level, COUNT(*)
            FROM dictionary_entries
            GROUP BY entry_type, jlpt_level
            ORDER BY entry_type, jlpt_level
        """)
        print("\ndictionary_entries:")
        print(f"  {'Type':<10} {'Level':<8} {'Count':>8}")
        print(f"  {'-'*30}")
        for row in cur.fetchall():
            print(f"  {str(row[0]):<10} {str(row[1]):<8} {row[2]:>8,}")

        # entry_relations by type
        cur.execute("""
            SELECT relation_type, COUNT(*)
            FROM entry_relations
            GROUP BY relation_type
            ORDER BY relation_type
        """)
        print("\nentry_relations:")
        print(f"  {'Type':<15} {'Count':>8}")
        print(f"  {'-'*25}")
        for row in cur.fetchall():
            print(f"  {str(row[0]):<15} {row[1]:>8,}")

        # examples count
        cur.execute("SELECT COUNT(*) FROM examples")
        count = cur.fetchone()[0]
        print(f"\nexamples: {count:,}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    verify_data()
