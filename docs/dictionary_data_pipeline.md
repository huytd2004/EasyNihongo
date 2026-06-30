# 📚 Dictionary Data Pipeline

## Tổng quan

Populate 3 bảng chính trong schema:

| Bảng | Nội dung | Nguồn |
|---|---|---|
| `dictionary_entries` | word / kanji | jmdict-simplified + kanjidic2-en JSON |
| `entry_relations` | kanji / radical / compound / synonym | kradfile JSON + tính toán |
| `examples` | Câu ví dụ JA–VI | Tatoeba corpus |

> [!NOTE]
> `entry_type = 'grammar'` không có nguồn free structured → nhập thủ công.

---

## 1. Nguồn dữ liệu thực tế

Tất cả đều lấy từ **[jmdict-simplified](https://github.com/scriptin/jmdict-simplified/releases/latest)** (release v3.6.x) — đã parse sẵn dạng JSON, không cần xử lý XML hay encoding EUC-JP.

| File | Kích thước | Nội dung |
|---|---|---|
| `jmdict-eng-{ver}.json.zip` | ~30MB zip / 112MB JSON | 217k từ vựng Nhật–Anh |
| `kanjidic2-en-{ver}.json.zip` | ~5MB zip / 15MB JSON | 10k kanji, có JLPT level và số nét |
| `kradfile-{ver}.json.zip` | ~100KB zip / 438KB JSON | Mapping kanji → bộ thủ (radical) |

**JLPT level cho words** — JMdict v3.6.x đã bỏ JLPT tags. Dùng bổ sung:

| File | Nguồn |
|---|---|
| `n3.csv`, `n4.csv`, `n5.csv` | [open-anki-jlpt-decks](https://github.com/jamsinclair/open-anki-jlpt-decks) (tự động tải) |

**Câu ví dụ** — Tatoeba:

| File | Kích thước |
|---|---|
| `sentences.tar.bz2` → `sentences.csv` | ~900MB → 716MB |
| `links.tar.bz2` → `links.csv` | ~200MB → 430MB |

---

## 2. Pipeline

```
BƯỚC 1: Download
  ├── jmdict-eng JSON       (jmdict-simplified GitHub releases)
  ├── kanjidic2-en JSON     (jmdict-simplified GitHub releases)
  ├── kradfile JSON         (jmdict-simplified GitHub releases)
  ├── JLPT CSVs N3/N4/N5   (open-anki-jlpt-decks, tự tải trong parse_jmdict.py)
  └── Tatoeba sentences + links (tatoeba.org/downloads)

BƯỚC 2: Parse
  ├── parse_jmdict.py   → lọc 4,215 words JLPT N3/N4/N5 (match với JLPT CSV)
  └── parse_kanjidic.py → lọc 1,026 kanji (jlptLevel 3/4 hoặc grade ≤ 6 → N5)

BƯỚC 3: Translate EN → VI
  └── translate_meanings.py (deep-translator + cache file)

BƯỚC 4: Build entry_relations
  ├── kanji    — word text chứa kanji nào → link sang kanji entry
  ├── radical  — kradfile.json: kanji → list bộ thủ
  ├── compound — word chia sẻ cùng kanji (tính toán)
  └── synonym  — JMdict sense.related field

BƯỚC 5: Tatoeba examples
  └── filter 8,450 cặp JA–VI → ghép với word entries → 6,940 examples

BƯỚC 6: Load PostgreSQL
  └── dictionary_entries → entry_relations → examples
```

---

## 3. Kết quả thực tế

| Bảng | N5 | N4 | N3 | Tổng |
|---|---|---|---|---|
| `dictionary_entries` (word) | 899 | 793 | 2,523 | **4,215** |
| `dictionary_entries` (kanji) | 742 | 103 | 181 | **1,026** |
| `entry_relations` (kanji) | — | — | — | **4,656** |
| `entry_relations` (radical) | — | — | — | **1,969** |
| `entry_relations` (compound) | — | — | — | **3,321** |
| `entry_relations` (synonym) | — | — | — | **226** |
| `examples` | — | — | — | **6,940** |

---

## 4. Scripts

```
ai/scripts/seed_dictionary/
├── download_sources.sh    # Tải JMdict, Kanjidic2, KradFile, Tatoeba
├── parse_jmdict.py        # Parse words + auto-download JLPT CSVs
├── parse_kanjidic.py      # Parse kanjidic2-en.json
├── translate_meanings.py  # deep-translator EN→VI với cache
├── build_relations.py     # Build 4 loại relations
├── import_examples.py     # Filter Tatoeba JA-VI pairs
├── load_to_postgres.py    # INSERT vào PostgreSQL (ON CONFLICT DO NOTHING)
├── main.py                # Runner tổng hợp
└── requirements.txt       # lxml pandas psycopg2-binary tqdm deep-translator python-dotenv
```

### Setup

```bash
cd ai/scripts/seed_dictionary
pip install -r requirements.txt

# Tải raw data
bash download_sources.sh
```

### Chạy pipeline

```bash
# Đầy đủ (dịch + examples, mất ~45 phút)
python main.py

# Bỏ dịch (dùng nghĩa EN, chạy nhanh)
python main.py --skip-translate

# Bỏ cả dịch lẫn examples (~10 giây)
python main.py --skip-translate --skip-examples

# Chỉ verify DB
python main.py --verify-only
```

### DB connection

Script đọc từ `DATABASE_URL` env. Fallback mặc định:
```
postgresql://postgres:123456@localhost:5432/datn
```

---

## 5. Lưu ý kỹ thuật

| Vấn đề | Giải pháp |
|---|---|
| JMdict v3.6.x không có JLPT tags | Match bằng `open-anki-jlpt-decks` CSV |
| Kanjidic2 N5 không có tag riêng | `grade ≤ 6` (tiểu học) → N5 |
| Dịch mất nhiều thời gian | Cache lưu tại `data/translation_cache.json`, tự bỏ qua entry đã dịch |
| Tatoeba nặng (~1GB) | Filter ngay trong pandas: chỉ giữ JA + VI sentences |
| Re-run idempotent | `ON CONFLICT DO NOTHING` — an toàn khi chạy lại |

> [!WARNING]
> **Grammar entries** không có nguồn free. Nhập thủ công vào CSV riêng rồi insert thẳng vào DB.
