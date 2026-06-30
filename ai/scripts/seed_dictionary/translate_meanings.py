"""
translate_meanings.py — Batch translate nghĩa EN → VI bằng deep-translator.

Dùng deep-translator (ổn định hơn googletrans):
  pip install deep-translator

Rate limiting:
  - Google Translate (free): ~100 requests/s, nhưng nên giới hạn để tránh block
  - Batch theo từng entry để tiết kiệm quota
"""
import time
import json
from pathlib import Path
from tqdm import tqdm


def translate_batch(
    entries: list[dict],
    batch_size: int = 100,
    sleep_between_batches: float = 1.0,
    cache_file: str = None,
) -> list[dict]:
    """
    Dịch nghĩa EN → VI cho tất cả entries.

    Args:
        entries: list[dict] với field "meaning_en"
        batch_size: Số entries mỗi batch (để xử lý lỗi từng phần)
        sleep_between_batches: Giây nghỉ giữa mỗi batch
        cache_file: Nếu chỉ định, lưu/đọc cache để tránh dịch lại khi restart

    Returns:
        entries với field "meaning_vn" đã được cập nhật
    """
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        raise ImportError("Vui lòng cài: pip install deep-translator")

    translator = GoogleTranslator(source="en", target="vi")

    # Load cache nếu có
    cache: dict[str, str] = {}
    if cache_file and Path(cache_file).exists():
        print(f"Loading translation cache from {cache_file}...")
        with open(cache_file, encoding="utf-8") as f:
            cache = json.load(f)
        print(f"Cache có {len(cache):,} entries")

    errors = 0
    translated = 0
    cache_hits = 0

    for i in tqdm(range(0, len(entries), batch_size), desc="Translating"):
        batch = entries[i : i + batch_size]

        for entry in batch:
            en_text = entry.get("meaning_en", "")
            if not en_text:
                continue

            # Check cache
            if en_text in cache:
                entry["meaning_vn"] = cache[en_text]
                cache_hits += 1
                continue

            try:
                vi_text = translator.translate(en_text)
                if vi_text:
                    entry["meaning_vn"] = vi_text
                    cache[en_text] = vi_text
                    translated += 1
                else:
                    entry["meaning_vn"] = en_text  # Fallback
            except Exception as e:
                errors += 1
                # Không print từng lỗi để tránh spam, chỉ giữ tiếng Anh
                entry["meaning_vn"] = en_text

            time.sleep(0.05)  # Nhẹ nhàng hơn, tránh rate limit

        # Lưu cache sau mỗi batch
        if cache_file and (i + batch_size) % (batch_size * 5) == 0:
            _save_cache(cache, cache_file)

        time.sleep(sleep_between_batches)

    # Lưu cache lần cuối
    if cache_file:
        _save_cache(cache, cache_file)

    print(f"\nTranslation complete:")
    print(f"  Translated: {translated:,}")
    print(f"  Cache hits: {cache_hits:,}")
    print(f"  Errors (kept EN): {errors:,}")

    return entries


def _save_cache(cache: dict, cache_file: str):
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_entries(
    entries: list[dict],
    cache_path: str = "data/translation_cache.json",
) -> list[dict]:
    """
    Convenience wrapper: dịch toàn bộ entries với caching.
    Cache được lưu tại cache_path để tránh dịch lại khi chạy lại script.
    """
    print(f"Chuẩn bị dịch {len(entries):,} entries...")

    # Đếm số entry cần dịch (chưa có meaning_vn khác meaning_en)
    need_translate = sum(
        1 for e in entries
        if e.get("meaning_en") and e.get("meaning_vn") == e.get("meaning_en")
    )
    print(f"Số entry cần dịch: {need_translate:,}")

    if need_translate == 0:
        print("Không có entry nào cần dịch!")
        return entries

    return translate_batch(
        entries,
        batch_size=100,
        sleep_between_batches=0.5,
        cache_file=cache_path,
    )


if __name__ == "__main__":
    # Test với một vài entries
    test_entries = [
        {"meaning_en": "to eat", "meaning_vn": "to eat"},
        {"meaning_en": "book; volume", "meaning_vn": "book; volume"},
        {"meaning_en": "school; educational institution", "meaning_vn": "school; educational institution"},
    ]
    result = translate_entries(test_entries, cache_path="data/test_cache.json")
    for e in result:
        print(f"EN: {e['meaning_en']} → VI: {e['meaning_vn']}")
