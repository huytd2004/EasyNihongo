"""
export_to_csv.py — Export graph từ Neo4j ra CSV để xem và đánh giá.

Xuất 2 file:
  1. graph_flat.csv  — View phẳng: mỗi dòng = 1 Sense, kèm Lexeme info + cues
  2. graph_stats.csv — Thống kê tổng hợp theo domain

Usage:
  python export_to_csv.py
  python export_to_csv.py --out /path/to/folder
  python export_to_csv.py --limit 500   # Chỉ lấy 500 Lexeme đầu
"""
import csv
import argparse
from pathlib import Path

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

try:
    from neo4j import GraphDatabase
except ImportError:
    raise ImportError("pip install neo4j")


# ── Queries ───────────────────────────────────────────────────────────────────

QUERY_FLAT = """
MATCH (lex:Lexeme)-[:HAS_SENSE]->(sense:Sense)-[:BELONGS_TO]->(dom:Domain)
OPTIONAL MATCH (sense)-[:SUPPORTED_BY]->(cue:Lexeme)
WITH lex, sense, dom, collect(DISTINCT cue.surface) AS cues
RETURN
  lex.surface                 AS surface,
  COALESCE(lex.reading, '')   AS reading,
  COALESCE(lex.pos, '')       AS pos,
  COALESCE(toString(lex.jlpt), '') AS jlpt,
  dom.name                    AS domain,
  sense.glossVi               AS glossVi,
  size(cues)                  AS cue_count,
  apoc_NOT_NEEDED_join(cues)  AS cues_str,
  cues                        AS cues_list
ORDER BY lex.surface, dom.name
LIMIT $limit
"""

# Không cần APOC — dùng Python để join cues
QUERY_FLAT_V2 = """
MATCH (lex:Lexeme)-[:HAS_SENSE]->(sense:Sense)-[:BELONGS_TO]->(dom:Domain)
OPTIONAL MATCH (sense)-[:SUPPORTED_BY]->(cue:Lexeme)
WITH lex, sense, dom, collect(DISTINCT cue.surface) AS cues
RETURN
  lex.surface                      AS surface,
  COALESCE(lex.reading, '')        AS reading,
  COALESCE(lex.pos, '')            AS pos,
  COALESCE(toString(lex.jlpt), '') AS jlpt,
  dom.name                         AS domain,
  COALESCE(sense.glossVi, '')      AS glossVi,
  size(cues)                       AS cue_count,
  cues                             AS cues_list
ORDER BY lex.surface, dom.name
LIMIT $limit
"""

QUERY_STATS = """
MATCH (lex:Lexeme)-[:HAS_SENSE]->(sense:Sense)-[:BELONGS_TO]->(dom:Domain)
WITH dom.name AS domain, count(DISTINCT lex) AS lexeme_count, count(sense) AS sense_count
RETURN domain, lexeme_count, sense_count
ORDER BY sense_count DESC
"""

QUERY_POLYSEMY = """
MATCH (lex:Lexeme)-[:HAS_SENSE]->(sense:Sense)
WITH lex, collect(DISTINCT sense.domain) AS domains, count(sense) AS total_senses
WHERE size(domains) >= 2
RETURN
  lex.surface    AS surface,
  lex.reading    AS reading,
  lex.pos        AS pos,
  total_senses   AS sense_count,
  size(domains)  AS domain_count,
  domains        AS all_domains
ORDER BY domain_count DESC, total_senses DESC
LIMIT $limit
"""


# ── Export functions ──────────────────────────────────────────────────────────

def export_flat(session, out_path: Path, limit: int) -> int:
    """Xuất flat view: mỗi dòng = 1 Sense."""
    rows = list(session.run(QUERY_FLAT_V2, limit=limit))

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        # utf-8-sig để Excel đọc được tiếng Nhật/Việt
        writer = csv.writer(f)
        writer.writerow([
            "surface", "reading", "pos", "jlpt",
            "domain", "glossVi",
            "cue_count", "cues (top 10)"
        ])
        for r in rows:
            cues_list = r["cues_list"] or []
            writer.writerow([
                r["surface"],
                r["reading"],
                r["pos"],
                r["jlpt"],
                r["domain"],
                r["glossVi"],
                r["cue_count"],
                " | ".join(cues_list[:10]),
            ])

    print(f"✅ {out_path.name}: {len(rows):,} rows")
    return len(rows)


def export_stats(session, out_path: Path) -> None:
    """Xuất thống kê domain."""
    rows = list(session.run(QUERY_STATS))

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["domain", "lexeme_count", "sense_count"])
        for r in rows:
            writer.writerow([r["domain"], r["lexeme_count"], r["sense_count"]])

    print(f"✅ {out_path.name}: {len(rows)} domains")


def export_polysemy(session, out_path: Path, limit: int) -> None:
    """Xuất danh sách từ đa nghĩa rõ nhất — dễ đánh giá chất lượng."""
    rows = list(session.run(QUERY_POLYSEMY, limit=limit))

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "surface", "reading", "pos",
            "sense_count", "domain_count", "domains"
        ])
        for r in rows:
            writer.writerow([
                r["surface"],
                r["reading"] or "",
                r["pos"] or "",
                r["sense_count"],
                r["domain_count"],
                " | ".join(sorted(r["all_domains"])),
            ])

    print(f"✅ {out_path.name}: {len(rows):,} polysemy lexemes")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export Neo4j graph to CSV")
    parser.add_argument("--out", type=str, default="data/export",
                        help="Thư mục output (default: data/export)")
    parser.add_argument("--limit", type=int, default=999_999,
                        help="Số Sense tối đa export (default: tất cả)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to Neo4j ({NEO4J_DATABASE}) ...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print(f"✅ Connected → database: {NEO4J_DATABASE}\n")

    with driver.session(database=NEO4J_DATABASE) as session:
        # 1. Flat view (toàn bộ senses)
        export_flat(session, out_dir / "graph_flat.csv", limit=args.limit)

        # 2. Domain stats
        export_stats(session, out_dir / "graph_stats.csv")

        # 3. Polysemy list (đánh giá chất lượng)
        export_polysemy(session, out_dir / "graph_polysemy.csv", limit=min(args.limit, 5000))

    driver.close()

    print(f"\n📁 Exported to: {out_dir.resolve()}")
    print("   graph_flat.csv     — Flat view: mỗi dòng = 1 Sense (surface + domain + glossVi + cues)")
    print("   graph_stats.csv    — Thống kê số Lexeme/Sense theo domain")
    print("   graph_polysemy.csv — Danh sách từ đa nghĩa (dễ đánh giá chất lượng ranking)")


if __name__ == "__main__":
    main()
