# Neo4j Knowledge Graph — Data Seeding Pipeline

Pipeline import dữ liệu **tiếng Nhật chuyên ngành** vào Neo4j, tạo knowledge graph
theo schema gồm 3 node (`Lexeme`, `Sense`, `Domain`) và 3 relationship
(`HAS_SENSE`, `BELONGS_TO`, `SUPPORTED_BY`).  
Pipeline này **hoàn toàn độc lập** với PostgreSQL pipeline.

---

## Kết quả thực tế (database: `datn-graph`)

| Metric | Giá trị |
|---|---|
| Domain | 6 |
| Lexeme (đa nghĩa chuyên ngành) | 3,321 |
| Sense (tổng) | 9,514 |
| SUPPORTED_BY edges (cues) | 24,153 |
| Specialized senses có ≥ 5 cue | 100% |
| Avg cues/sense | 6.1 |

---

## Bối cảnh & Mục tiêu

### Tại sao chỉ cần "từ đa nghĩa chuyên ngành"?
- Neo4j phục vụ **rank_sense** — phân biệt nghĩa (polysemy) dựa trên domain + cue context.
- Scoring: `score = 0.60 × domainMatch + 0.40 × cueMatch`
- Chỉ từ có **≥ 2 Sense thuộc domain khác nhau** mới hưởng lợi từ ranking.
- Từ đơn nghĩa phổ thông không cần đưa vào Neo4j.

### 6 Domains
`technology`, `medicine`, `academic`, `business`, `culture`, `general`

---

## Nguồn dữ liệu

### JMdict-simplified JSON

Nguồn chính. JMdict có trường `field` (= domain tags) trong mỗi `sense`:

```json
{
  "field": ["comp"],
  "gloss": [{"lang": "eng", "text": "cloud computing"}]
}
```

Mapping `field → domain`:

| JMdict field tags | Domain Neo4j |
|---|---|
| `comp`, `tech` | technology |
| `med`, `anat`, `biol`, `pharm` | medicine |
| `math`, `physics`, `chem`, `sci` | academic |
| `bus`, `finc`, `econ`, `law` | business |
| `music`, `art`, `food`, `sports`, `mahj`, `shogi`, `go`, `baseb`, `sumo` | culture |
| (không có field tag) | general |

### Bộ lọc đa nghĩa

Chỉ giữ Lexeme có **≥ 2 senses với domain khác nhau**:
- Giảm từ ~31,000 entry JMdict → **3,321 Lexeme** chất lượng cao
- Đảm bảo mọi Lexeme trong graph đều có giá trị phân biệt nghĩa

---

## Cue Mapping — Corpus-Derived

### Chiến lược

Cue mapping dùng **Tatoeba corpus** (248,678 câu tiếng Nhật) với Aho-Corasick
multi-pattern matching để tìm co-occurrence thực tế:

```
Với mỗi câu trong corpus:
  1. Tìm tất cả Lexeme surface xuất hiện cùng câu (Aho-Corasick)
  2. Với mỗi cặp (A, B) cùng câu: co_occ[A][B] += 1
  3. Top co-occurring surfaces → cues của Sense tương ứng
```

### Fallback khi corpus thiếu

Nếu Lexeme không xuất hiện trong corpus (từ chuyên ngành hiếm):
→ **Domain-peers fallback**: lấy ngẫu nhiên Lexeme khác **cùng domain** làm cues

```
Ví dụ: 伽藍堂 (culture domain, không có trong Tatoeba)
→ Cues = random sample từ [1,709 Lexeme khác có sense domain_culture]
```

### Thống kê coverage

| Loại | Số lượng |
|---|---|
| ✅ Corpus only (≥5 cue từ Tatoeba) | 594 senses |
| 🔀 Corpus + peers padded | 651 senses |
| ⚠️ Peers only (không có trong corpus) | 2,741 senses |
| ❌ Still zero | 0 senses |

---

## Scripts (`ai/scripts/seed_neo4j/`)

```
ai/scripts/seed_neo4j/
├── config.py                   # NEO4J_URI, DB, domain mappings
├── extract_from_jmdict.py      # Trích Lexeme + Sense từ JMdict, áp bộ lọc đa nghĩa
├── build_cue_mapping.py        # Cue mapping từ domain seeds (phương án cũ)
├── build_cue_from_corpus.py    # ⭐ Cue mapping corpus-derived (Tatoeba, Aho-Corasick)
├── translate_vi.py             # EN→VI (deep-translator, concurrent, cache)
├── generate_csvs.py            # → 4 CSV files
├── load_to_neo4j.py            # Import CSV → Neo4j (batch MERGE)
├── verify_neo4j.py             # Verification queries
├── export_to_csv.py            # Export graph → CSV để review
└── main.py                     # Runner tổng hợp (CLI)
```

### Cách chạy

```bash
cd ai/scripts/seed_neo4j/

# Full pipeline (mặc định dùng corpus cues)
python main.py --skip-translate   # nếu glossVi đã có cache

# Chỉ build cue từ corpus
python build_cue_from_corpus.py

# Chỉ load CSV vào Neo4j (đã có CSV sẵn)
python main.py --load-only

# Export để review
python export_to_csv.py           # → data/export/*.csv
```

### CLI flags của `main.py`

| Flag | Mô tả |
|---|---|
| `--skip-translate` | Bỏ bước dịch, dùng cache sẵn |
| `--no-corpus` | Dùng domain seed cues thay vì corpus |
| `--csv-only` | Chỉ generate CSV, không load Neo4j |
| `--load-only` | Chỉ load CSV đã có vào Neo4j |
| `--verify-only` | Chỉ chạy verification |
| `--jmdict PATH` | Đường dẫn custom đến jmdict-eng.json |

---

## Data Flow

```
jmdict-eng.json (đã có từ PostgreSQL pipeline)
       │
       ▼
extract_from_jmdict.py
       ├── lexemes_raw.json     (3,389 candidates)
       └── senses_raw.json      (9,563 senses với glossEn)
       │
       ▼
build_cue_from_corpus.py  ←── sentences.csv (Tatoeba 248k câu)
       └── cue_mapping_raw.json (24,225 cue rows)
       │
       ▼
translate_vi.py  ←── translation_cache_neo4j.json (cache)
       └── senses_translated.json (thêm glossVi)
       │
       ▼
generate_csvs.py
       ├── domains.csv           (6 rows)
       ├── lexemes.csv           (3,389 rows)
       ├── senses.csv            (9,563 rows)
       └── sense_cue_mapping.csv (24,225 rows)
       │
       ▼
load_to_neo4j.py → Neo4j `datn-graph` ✅
       │
       ▼
verify_neo4j.py → Báo cáo stats
```

---

## Verification Queries

```cypher
-- 1. Node counts
MATCH (n:Lexeme) RETURN count(n) AS lexeme_count;
MATCH (n:Sense)  RETURN count(n) AS sense_count;
MATCH (n:Domain) RETURN count(n) AS domain_count;

-- 2. Polysemy check (core requirement)
MATCH (l:Lexeme)-[:HAS_SENSE]->(s:Sense)-[:BELONGS_TO]->(d:Domain)
WITH l, collect(DISTINCT d.name) AS domains
WHERE size(domains) >= 2
RETURN count(l) AS polysemy_count;

-- 3. Cue coverage
MATCH (s:Sense)-[:BELONGS_TO]->(d:Domain)
WHERE d.name <> 'general'
OPTIONAL MATCH (s)-[:SUPPORTED_BY]->(cue:Lexeme)
WITH s, count(cue) AS cue_count
RETURN
  count(s)                                           AS total_specialized,
  sum(CASE WHEN cue_count >= 5 THEN 1 ELSE 0 END)   AS has_5plus_cues,
  avg(cue_count)                                     AS avg_cues,
  min(cue_count)                                     AS min_cues;

-- 4. Domain distribution
MATCH (s:Sense)-[:BELONGS_TO]->(d:Domain)
RETURN d.name AS domain, count(s) AS sense_count
ORDER BY sense_count DESC;
```

---

## Cấu hình Database

```
Neo4j URI:      bolt://localhost:7687
Database:       datn-graph
User:           neo4j
```

File `.env` tại `ai/scripts/seed_neo4j/.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678
NEO4J_DATABASE=datn-graph
```

> **Lưu ý:** Neo4j Community Edition không hỗ trợ `CREATE DATABASE` qua Cypher.
> Database `datn-graph` được tạo thủ công qua Neo4j Browser hoặc Neo4j Desktop trước khi chạy pipeline.
