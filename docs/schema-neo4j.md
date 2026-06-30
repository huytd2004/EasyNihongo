# Schema Neo4j — Knowledge Graph cho Translation Pipeline

## Nguyên tắc thiết kế

- **Neo4j**: lưu knowledge graph tĩnh, **read-only** trong mọi request.
- **Tokenization / sense ranking**: hoàn toàn in-memory (SudachiPy → MeCab → Regex).
- **Không persist** `Sentence`, `Token` vào Neo4j.
- Lịch sử dịch (nếu cần) → lưu **PostgreSQL** từ backend.

---

## 1. Node Types (3 loại)

### Lexeme

Đơn vị từ bề mặt. Đóng vai trò **cả từ vựng lẫn cue** cho các sense khác.

```
{
  lexemeId: String,    # e.g. "lex_半導体"
  surface:  String,    # e.g. "半導体"
  reading:  String,    # e.g. "はんどうたい"
  pos:      String,    # n | v | adj | adv
}
```

> **Lưu ý:** `jlpt` không có trong Neo4j graph.  
> JLPT data chỉ tồn tại trong PostgreSQL (`vocabulary` table).  
> Không dùng `jlpt` làm tiêu chí trong Neo4j pipeline.

### Sense

Một nghĩa cụ thể của Lexeme (xử lý polysemy).

```
{
  senseId: String,     # e.g. "sense_半導体_tech"
  glossVi: String,     # e.g. "bán dẫn"
  domain:  String,     # e.g. "domain_technology" (= domainId, lưu để lookup nhanh)
}
```

### Domain

Miền ngữ cảnh chuyên ngành.

```
{
  domainId: String,    # e.g. "domain_technology"
  name:     String,    # e.g. "technology"
}
```

**6 domains:** `technology`, `medicine`, `academic`, `business`, `culture`, `general`

---

## 2. Relationships

```
Lexeme -[:HAS_SENSE]-----→ Sense
Sense  -[:BELONGS_TO]----→ Domain
Sense  -[:SUPPORTED_BY]--→ Lexeme   ← cue: token đi cùng ngữ cảnh với sense này
```

**Ví dụ cho từ đa nghĩa `半導体`:**

```
(半導体:Lexeme)
  -[:HAS_SENSE]→ (sense_半導体_tech  {glossVi:"bán dẫn",  domain:"domain_technology"})
                    -[:BELONGS_TO]→ (Domain {name:"technology"})
                    -[:SUPPORTED_BY]→ (製造:Lexeme)
                    -[:SUPPORTED_BY]→ (プロセス:Lexeme)
                    -[:SUPPORTED_BY]→ (欠陥:Lexeme)

  -[:HAS_SENSE]→ (sense_半導体_gen   {glossVi:"chất bán dẫn", domain:"domain_general"})
                    -[:BELONGS_TO]→ (Domain {name:"general"})
```

> `Cue` không phải node riêng. `SUPPORTED_BY` trỏ thẳng đến `Lexeme` đã có.

---

## 3. Cue (SUPPORTED_BY) — Cách sinh

Cues được sinh từ **Tatoeba corpus** (248,678 câu) bằng Aho-Corasick co-occurrence:

```
Câu: "半導体の製造プロセスでは欠陥が生じる"
→ 半導体 co-occurs với: 製造, プロセス, 欠陥
→ sense_半導体_tech -[:SUPPORTED_BY]→ (製造), (プロセス), (欠陥)
```

**Fallback:** nếu Lexeme không xuất hiện trong corpus → lấy random peers cùng domain.

**Tiêu chuẩn tối thiểu:** mỗi specialized sense có **≥ 5 cues**.

---

## 4. Scoring Formula (runtime, in-memory)

```
score = 0.60 × domainMatch + 0.40 × cueMatch
```

| Thành phần | Tính | Trọng số |
|---|---|---|
| `domainMatch` | 1.0 nếu `sense.domain` ∈ `detected_domains`, else 0 | 0.60 |
| `cueMatch` | `count(cue.surface ∈ neighbor_surfaces) / total_cues` | 0.40 |

`neighbor_surfaces` = tất cả token surfaces trong đoạn văn đầu vào.

Sense có score cao nhất = `top_sense` → đưa vào prompt LLM.

---

## 5. Neo4j Queries

### Pass 1 — Lấy tất cả senses (detect domain)

```cypher
UNWIND $tokenSurfaces AS surface
MATCH (lex:Lexeme {surface: surface})
  -[:HAS_SENSE]->(sense:Sense)
  -[:BELONGS_TO]->(dom:Domain)
OPTIONAL MATCH (sense)-[:SUPPORTED_BY]->(cue:Lexeme)
WITH surface, lex, sense, dom,
     collect(DISTINCT cue.surface) AS cues
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
-- Thêm WHERE để filter domain (giữ lại general để có fallback)
WHERE dom.name IN $domains OR dom.name = 'general'
```

---

## 6. Import Data

### Thứ tự import (bắt buộc)

```
1. Domain     → CREATE INDEX ON Domain(name)
2. Lexeme     → CREATE INDEX ON Lexeme(surface)
3. Sense + HAS_SENSE + BELONGS_TO
4. SUPPORTED_BY (cue edges)
```

### CSV Format

**domains.csv**
```
domainId,name
domain_technology,technology
domain_medicine,medicine
domain_academic,academic
domain_business,business
domain_culture,culture
domain_general,general
```

**lexemes.csv**
```
lexemeId,surface,reading,pos
lex_半導体,半導体,はんどうたい,n
lex_製造,製造,せいぞう,n
```

**senses.csv**
```
senseId,glossVi,domain,lexemeId
sense_半導体_tech,bán dẫn,domain_technology,lex_半導体
sense_半導体_gen,chất bán dẫn,domain_general,lex_半導体
```

**sense_cue_mapping.csv**
```
senseId,cueSurface
sense_半導体_tech,製造
sense_半導体_tech,プロセス
sense_半導体_tech,欠陥
```

### Cypher Import

```cypher
// 1. Domain
LOAD CSV WITH HEADERS FROM "file:///domains.csv" AS row
MERGE (d:Domain {domainId: row.domainId})
SET d.name = row.name;
CREATE INDEX IF NOT EXISTS FOR (d:Domain) ON (d.name);

// 2. Lexeme
LOAD CSV WITH HEADERS FROM "file:///lexemes.csv" AS row
MERGE (l:Lexeme {lexemeId: row.lexemeId})
SET l.surface = row.surface,
    l.reading = row.reading,
    l.pos     = row.pos;
CREATE INDEX IF NOT EXISTS FOR (l:Lexeme) ON (l.surface);

// 3. Sense + HAS_SENSE + BELONGS_TO
LOAD CSV WITH HEADERS FROM "file:///senses.csv" AS row
MATCH (l:Lexeme {lexemeId: row.lexemeId})
MATCH (d:Domain {domainId: row.domain})
MERGE (s:Sense  {senseId:  row.senseId})
SET s.glossVi = row.glossVi,
    s.domain  = row.domain
MERGE (l)-[:HAS_SENSE]->(s)
MERGE (s)-[:BELONGS_TO]->(d);

// 4. SUPPORTED_BY (cue edges)
LOAD CSV WITH HEADERS FROM "file:///sense_cue_mapping.csv" AS row
MATCH (s:Sense   {senseId: row.senseId})
MATCH (cue:Lexeme {surface: row.cueSurface})
MERGE (s)-[:SUPPORTED_BY]->(cue);
```

---

## 7. Tiêu chuẩn dữ liệu

| Điều kiện | Lý do |
|---|---|
| Lexeme có **≥ 2 Sense** khác domain | Ranking mới có ý nghĩa |
| Mỗi Sense chuyên ngành có **≥ 5 cue** | Cue match ổn định hơn |
| Mỗi Sense phải có `domain` | Thiếu → domainMatch = 0 |
| `cueSurface` phải là surface của Lexeme thực | SUPPORTED_BY phải trỏ đến node tồn tại |

---

## 8. Tóm tắt

| Node | Vai trò | Bắt buộc |
|---|---|---|
| `Lexeme` | Từ vựng + cue cho sense khác | ✅ |
| `Sense` | Nghĩa + domain + glossVi | ✅ |
| `Domain` | Domain matching (W=0.60) | ✅ |

| Relationship | Ý nghĩa |
|---|---|
| `Lexeme -[:HAS_SENSE]→ Sense` | Từ có nghĩa nào |
| `Sense -[:BELONGS_TO]→ Domain` | Nghĩa thuộc miền nào |
| `Sense -[:SUPPORTED_BY]→ Lexeme` | Từ nào đi cùng ngữ cảnh → tín hiệu phân biệt nghĩa |

> Nếu cần tiebreak giữa 2 sense cùng domain → thêm `confidenceBase: Float` vào `Sense`.
