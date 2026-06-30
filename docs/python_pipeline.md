# Python Pipeline — Dịch Đoạn Văn Chuyên Ngành Nhật → Việt

## Tổng quan

Pipeline **stateless** dịch văn bản tiếng Nhật chuyên ngành sang tiếng Việt, tận dụng
Knowledge Graph Neo4j để cung cấp context nghĩa chính xác cho LLM.

**Nguyên tắc cốt lõi:**
- Neo4j: **read-only**, chỉ truy vấn graph tĩnh — không tạo node, không ghi dữ liệu.
- Tokenization, domain detection, sense ranking: hoàn toàn **in-memory**.
- Lịch sử bản dịch (nếu cần) lưu PostgreSQL tại tầng backend — pipeline không quan tâm.

---

## 1. Luồng xử lý

```
Input text (tiếng Nhật)
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 1: Tokenize (SudachiPy → MeCab → Regex fallback)         │
│          Tách thành list token surfaces                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 2a: Neo4j Pass 1 — batch query với ['general']            │
│           Lấy TẤT CẢ senses + cues cho mọi token               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 2b: Detect Domain — frequency vote từ graph evidence      │
│           Đếm token/domain, chọn domain có vote ≥ 30% max       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 3: Neo4j Pass 2 — re-query với detected domains           │
│          (bỏ qua nếu domain = ['general'])                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 4: Rank Senses (in-memory)                                │
│          Score = W_DOMAIN * domainMatch + W_CUE * cueRatio      │
│          W_DOMAIN=0.60, W_CUE=0.40                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 5: Build Prompt                                           │
│          Structured prompt kèm graph evidence (glossVi, domain) │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bước 6: LLM Translate (Gemini 2.5 Flash)                       │
│          Trả về JSON: {translation, notes}                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    Output JSON (xem mục 4)
```

---

## 2. Tokenizer

Thứ tự ưu tiên khi tokenize:

| Priority | Tokenizer | Ghi chú |
|---|---|---|
| 1 | **SudachiPy** (Mode B) | Tốt nhất, tách katakana compound: `クラウドコンピューティング` → `クラウド` + `コンピューティング` |
| 2 | **MeCab** | Fallback nếu Sudachi không có |
| 3 | **Regex** | Fallback cuối: tách theo boundary Kanji/Katakana/Hiragana/Latin |

> **Lý do dùng Mode B (standard split):** Graph được index theo từ đơn (e.g. `クラウド`, `サーバー`).
> Mode C (long unit) giữ nguyên compound → không match được trong graph.

Stop POS bị lọc bỏ: `助詞`, `助動詞`, `補助記号`, `空白`, `感動詞`.

---

## 3. Domain Detection — Frequency Vote

Sau khi có `graph_evidence` từ pass 1, tính domain bằng **đếm số token** có sense thuộc domain đó:

```
Ví dụ: "クラウドコンピューティングは、インターネットを通じてサーバーやストレージ..."

Token → non-general domains:
  クラウド   → [technology]
  サーバー   → [technology, culture]
  サービス   → [technology, business]

Domain vote count:
  domain_technology : 3 votes  ← winner
  domain_culture    : 1 vote
  domain_business   : 1 vote

threshold = 0.30 → min_votes = max(1, 3×0.30) = 0.9 → round up = 1
  technology: 3 ≥ 1 ✅
  culture:    1 ≥ 1 ✅ (vừa đủ ngưỡng)
  business:   1 ≥ 1 ✅

→ detected = ['domain_technology', 'domain_culture', 'domain_business']
```

**Tại sao không dùng keyword hardcode:**
- Keyword list nhanh stale, khó maintain.
- Frequency vote tự động scale theo từ vựng thực trong văn bản.
- Từ đa nghĩa chỉ đóng góp 1 vote/domain (không inflate).

**Tại sao bỏ qua `general`:**
- Domain `general` có mặt ở hầu hết mọi từ → không discriminative.

---

## 4. Sense Ranking

Sau khi có `graph_evidence` với đúng domains:

```python
score = 0.0

# Domain match (60%)
if sense.domain in detected_domains:
    score += 0.60

# Cue match (40%) — tỉ lệ cue của sense xuất hiện trong đoạn
if cues:
    matched = count(c for c in cues if c in neighbor_surfaces)
    score += 0.40 * (matched / len(cues))
```

`neighbor_surfaces` = tất cả token surfaces trong đoạn văn (dùng làm ngữ cảnh).

---

## 5. Key Vocabulary

Token được đưa vào `keyVocabulary` nếu thỏa một trong hai điều kiện:

| Điều kiện | Ý nghĩa |
|---|---|
| `is_domain_specific` | top_sense thuộc domain được detect |
| `is_polysemy` | có ít nhất 2 senses với score > 0 |

> **Lưu ý:** JLPT không có trong Neo4j graph (chỉ tồn tại ở PostgreSQL) → không dùng làm tiêu chí.

Schema của mỗi item trong `keyVocabulary`:
```json
{
  "surface": "半導体",
  "reading": "はんどうたい",
  "glossVi": "bán dẫn",
  "domain":  "domain_technology",
  "score":   0.85
}
```

---

## 6. Neo4j Query

### Pass 1 — Lấy tất cả senses (để detect domain)
```cypher
UNWIND $tokenSurfaces AS surface
MATCH (lex:Lexeme {surface: surface})
  -[:HAS_SENSE]->(sense:Sense)
  -[:BELONGS_TO]->(dom:Domain)
OPTIONAL MATCH (sense)-[:SUPPORTED_BY]->(cue:Lexeme)
WITH surface, lex, sense, dom, collect(DISTINCT cue.surface) AS cues
RETURN
  surface        AS token,
  lex.reading    AS reading,
  sense.senseId  AS senseId,
  sense.glossVi  AS glossVi,
  dom.name       AS domain,
  cues
ORDER BY token
```

### Pass 2 — Filter theo domain đã detect
```cypher
-- Thêm WHERE clause:
WHERE dom.name IN $domains OR dom.name = 'general'
```

---

## 7. Output Schema

```json
{
  "translation":     "Điện toán đám mây là công nghệ...",
  "keyVocabulary": [
    {
      "surface": "クラウド",
      "reading": "クラウド",
      "glossVi": "điện toán đám mây; dịch vụ đám mây",
      "domain":  "domain_technology",
      "score":   0.6
    }
  ],
  "notes": [
    {"type": "technical", "token": "クラウド", "content": "..."}
  ],
  "detectedDomains": ["domain_technology"]
}
```

> `warnings` field đã bị loại bỏ — không còn `_post_check` consistency check vì quá nhiều
> false positive (POS mismatch, synonym, word form variation).

---

## 8. Graph Schema (Neo4j — `datn-graph`)

```
(Lexeme) -[:HAS_SENSE]->  (Sense) -[:BELONGS_TO]-> (Domain)
(Sense)  -[:SUPPORTED_BY]->(Lexeme)   ← cue lexemes
```

| Node | Properties |
|---|---|
| `Lexeme` | `lexemeId`, `surface`, `reading`, `pos` |
| `Sense` | `senseId`, `glossVi`, `domain`, `domainKey` |
| `Domain` | `domainId`, `name` |

**Thống kê hiện tại (database: `datn-graph`):**

| Metric | Giá trị |
|---|---|
| Lexeme | 3,321 |
| Sense | 9,514 |
| SUPPORTED_BY edges | 24,153 |
| Cue coverage (specialized) | 100% |
| Avg cues/sense | 6.1 |

**6 domains:** `technology`, `medicine`, `academic`, `business`, `culture`, `general`

---

## 9. Cách chạy

### Từ Java Backend (subprocess)
```yaml
# backend/src/main/resources/application.yaml
app:
  translate:
    python-command: /path/to/ai/.venv/bin/python
    ai-root: /path/to/ai
```
Java chạy:
```
python -m python_pipeline.runner --text "..." --json
```

### Trực tiếp từ CLI
```bash
cd ai/
.venv/bin/python -m python_pipeline.runner \
  --text "クラウドコンピューティングは..." \
  --json
```

### Dependency
```
sudachipy        # tokenizer chính
sudachidict-core # từ điển Sudachi
neo4j            # Neo4j Python driver
google-generativeai  # Gemini API
```

---

## 10. Thiết kế quyết định

| Quyết định | Lý do |
|---|---|
| Stateless pipeline (không LangGraph state graph) | Đơn giản, dễ debug, phù hợp với subprocess invocation từ Java |
| 2-pass Neo4j query | Pass 1 lấy hết để detect domain; Pass 2 lấy đúng domain để rank |
| Frequency vote thay keyword matching | Không cần maintain keyword list, tự adapt theo vocabulary |
| Bỏ `_post_check` | Quá nhiều false positive: POS mismatch, synonym, word form |
| Sudachi Mode B thay Mode C | Graph index từ đơn, Mode C giữ compound → không match |
| Bỏ JLPT từ keyVocabulary | JLPT không có trong Neo4j (chỉ PostgreSQL), luôn = null |
