"""
translate_vi.py — Dịch glossEn → glossVi cho Sense entries (phiên bản tối ưu).

Cải tiến so với v1:
- Deduplicate: chỉ dịch các glossEn UNIQUE → giảm ~60-70% API calls
- Concurrent: ThreadPoolExecutor với max 5 worker (tránh rate-limit)
- Cache: data/translation_cache_neo4j.json (riêng với PostgreSQL pipeline)
- Retry + exponential backoff tự động

Ước tính: ~2,000 unique glossEn → ~20-30 phút (thay vì 2.5 tiếng).
"""
import json
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from config import NEO4J_DIR, TRANS_CACHE

try:
    from deep_translator import GoogleTranslator
except ImportError:
    raise ImportError("Cần cài deep-translator: pip install deep-translator")

# ── Thread-safe cache ─────────────────────────────────────────────────────────
_cache_lock = threading.Lock()

def _load_cache(path: Path) -> dict[str, str]:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, str], path: Path) -> None:
    with _cache_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)


def _translate_one(text: str, retries: int = 4) -> str:
    """Dịch 1 text EN→VI, retry với exponential backoff."""
    for attempt in range(retries):
        try:
            translator = GoogleTranslator(source="en", target="vi")
            result = translator.translate(text)
            return result or text
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s, 8s
                time.sleep(wait)
            else:
                # Giữ nguyên EN nếu thất bại hoàn toàn
                return text
    return text


# ── Main ──────────────────────────────────────────────────────────────────────

def translate_senses(
    out_dir: Path = NEO4J_DIR,
    cache_path: Path = TRANS_CACHE,
    max_workers: int = 5,
    save_interval: int = 100,
) -> list[dict]:
    """
    Dịch glossEn → glossVi với deduplicate + concurrent threading.

    Args:
        out_dir:       Thư mục data/neo4j/
        cache_path:    File cache JSON
        max_workers:   Số thread song song (mặc định 5, tối đa nên là 8)
        save_interval: Lưu cache mỗi N translations

    Returns:
        list[dict] senses đã dịch
    """
    sense_path = out_dir / "senses_raw.json"
    if not sense_path.exists():
        raise FileNotFoundError("Cần chạy extract_from_jmdict.py trước.")

    with open(sense_path, encoding="utf-8") as f:
        senses: list[dict] = json.load(f)

    cache = _load_cache(cache_path)
    print(f"Senses tổng cộng:    {len(senses):,}")
    print(f"Cache hiện tại:      {len(cache):,} entries")

    # ── Step 1: Deduplicate ───────────────────────────────────────────────────
    all_gloss_en: set[str] = set()
    for s in senses:
        g = s.get("glossEn", "").strip()
        if g:
            all_gloss_en.add(g)

    # Loại bỏ những gì đã có trong cache
    need_translate: list[str] = [g for g in sorted(all_gloss_en) if g not in cache]

    print(f"Unique glossEn:      {len(all_gloss_en):,}")
    print(f"Đã có trong cache:   {len(all_gloss_en) - len(need_translate):,}")
    print(f"Cần dịch:            {len(need_translate):,}")
    print(f"Workers:             {max_workers}")
    print()

    if not need_translate:
        print("✅ Tất cả đã có trong cache, bỏ qua bước dịch.")
    else:
        # ── Step 2: Concurrent translation ───────────────────────────────────
        translated_count = 0

        with tqdm(total=len(need_translate), desc="Translating", unit="text") as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_text = {
                    executor.submit(_translate_one, text): text
                    for text in need_translate
                }

                for future in as_completed(future_to_text):
                    text   = future_to_text[future]
                    result = future.result()

                    with _cache_lock:
                        cache[text] = result
                    translated_count += 1
                    pbar.update(1)

                    # Save cache định kỳ
                    if translated_count % save_interval == 0:
                        _save_cache(cache, cache_path)

        # Final save
        _save_cache(cache, cache_path)
        print(f"\n✅ Đã dịch {translated_count:,} texts mới")
        print(f"   Cache: {cache_path} ({len(cache):,} entries)")

    # ── Step 3: Apply cache to all senses ────────────────────────────────────
    print("\nApplying translations to senses...")
    miss = 0
    for s in senses:
        gloss_en = s.get("glossEn", "").strip()
        if not gloss_en:
            s["glossVi"] = ""
            continue
        s["glossVi"] = cache.get(gloss_en, gloss_en)
        if gloss_en not in cache:
            miss += 1

    if miss:
        print(f"  ⚠️  {miss} senses không có translation (giữ EN)")

    # Save translated senses
    out_path = out_dir / "senses_translated.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(senses, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved: {out_path}")
    return senses


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=5, help="Số thread (default: 5)")
    args = parser.parse_args()
    translate_senses(max_workers=args.workers)
