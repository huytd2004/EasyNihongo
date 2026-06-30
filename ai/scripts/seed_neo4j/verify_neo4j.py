"""
verify_neo4j.py — Kiểm tra graph Neo4j sau khi import.

Chạy các Cypher query để verify:
1. Count nodes/relationships
2. Polysemy check (Lexeme có ≥2 sense khác domain)
3. Cue coverage (Sense chuyên ngành có ≥5 cue)
4. Sample batch query (từ schema-neo4j.md §4)
5. Domain distribution
"""
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, MIN_CUES_PER_SENSE

try:
    from neo4j import GraphDatabase
except ImportError:
    raise ImportError("Cần cài neo4j driver: pip install neo4j")


SAMPLE_SURFACES = ["半導体", "製造", "欠陥", "性能", "データ", "治療", "研究"]


def verify(driver) -> dict:
    results = {}

    with driver.session(database=NEO4J_DATABASE) as session:
        # ── 1. Node counts ────────────────────────────────────────────────
        print("── 1. Node & Relationship Counts ──")
        for label in ["Domain", "Lexeme", "Sense"]:
            count = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
            results[f"count_{label}"] = count
            print(f"  {label:10s}: {count:,}")

        for rel in ["HAS_SENSE", "BELONGS_TO", "SUPPORTED_BY"]:
            count = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
            results[f"count_{rel}"] = count
            print(f"  [:{rel}]: {count:,}")

        # ── 2. Polysemy check ─────────────────────────────────────────────
        print("\n── 2. Polysemy Check (Lexeme có ≥2 sense khác domain) ──")
        q = """
        MATCH (l:Lexeme)-[:HAS_SENSE]->(s:Sense)
        WITH l, collect(DISTINCT s.domain) AS domains
        WHERE size(domains) >= 2
        RETURN count(l) AS polysemy_count
        """
        poly_count = session.run(q).single()["polysemy_count"]
        results["polysemy_count"] = poly_count
        print(f"  Lexeme đa nghĩa (≥2 domain): {poly_count:,}")

        # ── 3. Cue coverage ───────────────────────────────────────────────
        print(f"\n── 3. Cue Coverage (Sense chuyên ngành, ≥{MIN_CUES_PER_SENSE} cue) ──")
        q = """
        MATCH (s:Sense)-[:SUPPORTED_BY]->(c:Lexeme)
        WHERE s.domain <> 'domain_general'
        WITH s, count(c) AS cue_count
        RETURN
          count(s)                      AS total_specialized_senses,
          sum(CASE WHEN cue_count >= $min THEN 1 ELSE 0 END) AS senses_with_enough_cues,
          avg(cue_count)                AS avg_cues,
          min(cue_count)                AS min_cues,
          max(cue_count)                AS max_cues
        """
        row = session.run(q, min=MIN_CUES_PER_SENSE).single()
        if row:
            total = row["total_specialized_senses"]
            enough = row["senses_with_enough_cues"]
            pct = (enough / total * 100) if total else 0
            print(f"  Specialized senses total: {total:,}")
            print(f"  Có ≥{MIN_CUES_PER_SENSE} cue:  {enough:,} ({pct:.1f}%)")
            print(f"  Avg cues/sense: {row['avg_cues']:.1f}")
            print(f"  Min/Max cues:   {row['min_cues']} / {row['max_cues']}")
            results["cue_coverage_pct"] = round(pct, 1)

        # ── 4. Domain distribution ────────────────────────────────────────
        print("\n── 4. Domain Distribution ──")
        q = """
        MATCH (s:Sense)-[:BELONGS_TO]->(d:Domain)
        RETURN d.name AS domain, count(s) AS sense_count
        ORDER BY sense_count DESC
        """
        for record in session.run(q):
            print(f"  {record['domain']:12s}: {record['sense_count']:,} senses")

        # ── 5. Sample batch query (schema-neo4j.md §4) ────────────────────
        print(f"\n── 5. Sample Batch Query ──")
        q = """
        UNWIND $surfaces AS surface
        MATCH (lex:Lexeme {surface: surface})
          -[:HAS_SENSE]->(sense:Sense)
        OPTIONAL MATCH (sense)-[:BELONGS_TO]->(dom:Domain)
        OPTIONAL MATCH (sense)-[:SUPPORTED_BY]->(cue:Lexeme)
        WITH surface, lex, sense, dom,
             collect(DISTINCT cue.surface)[..5] AS cues
        RETURN
          surface       AS token,
          lex.reading   AS reading,
          sense.glossVi AS glossVi,
          dom.name      AS domain,
          cues
        ORDER BY token
        LIMIT 20
        """
        found_surfaces = set()
        rows = list(session.run(q, surfaces=SAMPLE_SURFACES))
        if rows:
            for record in rows:
                surface = record["token"]
                if surface not in found_surfaces:
                    print(f"\n  [{surface}] reading={record['reading']}")
                    found_surfaces.add(surface)
                print(f"    domain={record['domain']}, gloss={record['glossVi']}")
                print(f"    cues={record['cues']}")
        else:
            print(f"  WARN: Không tìm thấy kết quả cho {SAMPLE_SURFACES}")
            print(f"  (Dữ liệu mẫu hardcode có thể không có trong graph)")

        print(f"\n✅ Verification complete!")
        return results


def main():
    print(f"Connecting to {NEO4J_URI} ...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        results = verify(driver)

        # Summary verdict
        print("\n── Verdict ──")
        poly = results.get("polysemy_count", 0)
        cue_pct = results.get("cue_coverage_pct", 0)

        if poly >= 100:
            print(f"  ✅ Polysemy: {poly:,} (tốt, ≥100)")
        else:
            print(f"  ⚠️  Polysemy: {poly:,} (cần ≥100 để ranking có ý nghĩa)")

        if cue_pct >= 80:
            print(f"  ✅ Cue coverage: {cue_pct}% (tốt)")
        else:
            print(f"  ⚠️  Cue coverage: {cue_pct}% (cần ≥80%)")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
