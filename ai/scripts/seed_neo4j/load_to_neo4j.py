"""
load_to_neo4j.py — Import 4 CSV files vào Neo4j theo đúng thứ tự schema.

Thứ tự import (dependency order):
  1. Domain
  2. Lexeme
  3. Sense + HAS_SENSE (Lexeme→Sense) + BELONGS_TO (Sense→Domain)
  4. SUPPORTED_BY (Sense→Lexeme cue)

Sử dụng Python Neo4j driver (không dùng LOAD CSV file:// để tránh cấu hình
Neo4j import directory). Thay vào đó, đọc CSV bằng Python và chạy Cypher MERGE.
"""
import csv
import sys
from pathlib import Path
from tqdm import tqdm

from config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, NEO4J_DIR,
)

try:
    from neo4j import GraphDatabase, Driver
except ImportError:
    raise ImportError("Cần cài neo4j driver: pip install neo4j")


# ── Cypher queries ────────────────────────────────────────────────────────────

CREATE_INDEXES = """
CREATE INDEX lexeme_surface IF NOT EXISTS FOR (l:Lexeme) ON (l.surface);
CREATE INDEX lexeme_id IF NOT EXISTS FOR (l:Lexeme) ON (l.lexemeId);
CREATE INDEX sense_id IF NOT EXISTS FOR (s:Sense) ON (s.senseId);
CREATE INDEX domain_id IF NOT EXISTS FOR (d:Domain) ON (d.domainId);
CREATE INDEX domain_name IF NOT EXISTS FOR (d:Domain) ON (d.name);
"""

MERGE_DOMAIN = """
MERGE (d:Domain {domainId: $domainId})
SET d.name = $name
"""

MERGE_LEXEME = """
MERGE (l:Lexeme {lexemeId: $lexemeId})
SET l.surface  = $surface,
    l.reading  = $reading,
    l.pos      = $pos,
    l.jlpt     = CASE WHEN $jlpt <> '' THEN toInteger($jlpt) ELSE null END
"""

MERGE_SENSE = """
MATCH (l:Lexeme {lexemeId: $lexemeId})
MATCH (d:Domain {domainId: $domain})
MERGE (s:Sense {senseId: $senseId})
SET s.glossVi = $glossVi,
    s.domain  = $domain
MERGE (l)-[:HAS_SENSE]->(s)
MERGE (s)-[:BELONGS_TO]->(d)
"""

MERGE_CUE = """
MATCH (s:Sense {senseId: $senseId})
MERGE (cue:Lexeme {surface: $cueSurface})
MERGE (s)-[:SUPPORTED_BY]->(cue)
"""


# ── Loader ────────────────────────────────────────────────────────────────────

def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _run_in_batches(
    driver: "Driver",
    query: str,
    rows: list[dict],
    batch_size: int = 500,
    desc: str = "Importing",
    database: str = "neo4j",
) -> int:
    total = 0
    with driver.session(database=database) as session:
        for i in tqdm(range(0, len(rows), batch_size), desc=desc, unit="batch"):
            batch = rows[i : i + batch_size]
            for row in batch:
                session.run(query, **row)
            total += len(batch)
    return total


def load_to_neo4j(data_dir: Path = NEO4J_DIR) -> None:
    csv_dir = data_dir

    # Check files
    required = ["domains.csv", "lexemes.csv", "senses.csv", "sense_cue_mapping.csv"]
    for fname in required:
        if not (csv_dir / fname).exists():
            raise FileNotFoundError(
                f"Không tìm thấy {fname}. Chạy generate_csvs.py trước."
            )

    print(f"Connecting to Neo4j: {NEO4J_URI} (database: {NEO4J_DATABASE})")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # Verify connection
        driver.verify_connectivity()
        print("✅ Neo4j connected\n")

        # ── Create database if not exists ────────────────────────────────────
        if NEO4J_DATABASE != "neo4j":
            print(f"Ensuring database '{NEO4J_DATABASE}' exists...")
            try:
                with driver.session(database="system") as session:
                    session.run(f"CREATE DATABASE `{NEO4J_DATABASE}` IF NOT EXISTS")
                print(f"✅ Database ready\n")
            except Exception as e:
                # Community Edition không hỗ trợ CREATE DATABASE
                # Database đã được tạo trước → tiếp tục
                print(f"  ℹ️  Skipped DB creation ({type(e).__name__}): using existing.\n")

        def _session():
            return driver.session(database=NEO4J_DATABASE)

        # ── Create indexes ──────────────────────────────────────────────────
        print("Creating indexes...")
        with driver.session(database=NEO4J_DATABASE) as session:
            for stmt in CREATE_INDEXES.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    session.run(stmt)
        print("✅ Indexes created\n")

        # ── 1. Domains ──────────────────────────────────────────────────────
        domains = _read_csv(csv_dir / "domains.csv")
        print(f"Step 1: Importing {len(domains)} domains...")
        _run_in_batches(driver, MERGE_DOMAIN, domains, desc="  Domains", database=NEO4J_DATABASE)
        print(f"✅ {len(domains)} domains imported\n")

        # ── 2. Lexemes ──────────────────────────────────────────────────────
        lexemes = _read_csv(csv_dir / "lexemes.csv")
        print(f"Step 2: Importing {len(lexemes):,} lexemes...")
        _run_in_batches(driver, MERGE_LEXEME, lexemes, batch_size=200, desc="  Lexemes", database=NEO4J_DATABASE)
        print(f"✅ {len(lexemes):,} lexemes imported\n")

        # ── 3. Senses + HAS_SENSE + BELONGS_TO ──────────────────────────────
        senses = _read_csv(csv_dir / "senses.csv")
        print(f"Step 3: Importing {len(senses):,} senses + relationships...")
        _run_in_batches(driver, MERGE_SENSE, senses, batch_size=200, desc="  Senses", database=NEO4J_DATABASE)
        print(f"✅ {len(senses):,} senses imported\n")

        # ── 4. Cue mapping SUPPORTED_BY ─────────────────────────────────────
        cues = _read_csv(csv_dir / "sense_cue_mapping.csv")
        print(f"Step 4: Importing {len(cues):,} SUPPORTED_BY edges...")
        _run_in_batches(driver, MERGE_CUE, cues, batch_size=500, desc="  Cues", database=NEO4J_DATABASE)
        print(f"✅ {len(cues):,} cue edges imported\n")

        # ── Summary count ────────────────────────────────────────────────────
        print("── Final count ──")
        with driver.session(database=NEO4J_DATABASE) as session:
            for label in ["Domain", "Lexeme", "Sense"]:
                count = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
                print(f"  {label:8s}: {count:,}")
            for rel in ["HAS_SENSE", "BELONGS_TO", "SUPPORTED_BY"]:
                count = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
                print(f"  [:{rel}]: {count:,}")

        print("\n🎉 Neo4j import complete!")

    finally:
        driver.close()


if __name__ == "__main__":
    load_to_neo4j()
