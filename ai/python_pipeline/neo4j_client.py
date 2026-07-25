from neo4j import GraphDatabase
try:
    from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DATABASE
except ImportError:
    from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DATABASE


class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None, database=None):
        self._uri = uri or NEO4J_URI
        self._user = user or NEO4J_USER
        self._password = password or NEO4J_PASS
        self._database = database or NEO4J_DATABASE
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def close(self):
        self._driver.close()

    def batch_query_by_surfaces(self, token_surfaces: list[str], detected_domains: list[str]) -> list[dict]:
        """
        Stateless batch query: lấy sense evidence cho list token surfaces.
        Chỉ lấy domain + cues (phục vụ rank đơn giản hoá).
        Không cần Sentence/Token node trong Neo4j.

        Nếu detected_domains = ['general'] → lấy TẤT CẢ senses (pass 1, dùng để detect domain).
        Nếu detected_domains có domain cụ thể → chỉ lấy senses thuộc domain đó + general.
        """
        # Khi pass 1 (general) → lấy hết
        # Khi pass 2 (domain cụ thể) → filter, nhưng luôn include general để có context đầy đủ
        include_domains = detected_domains if detected_domains != ['general'] else None

        if include_domains:
            q = """
            UNWIND $tokenSurfaces AS surface
            MATCH (lex:Lexeme {surface: surface})
              -[:HAS_SENSE]->(sense:Sense)
              -[:BELONGS_TO]->(dom:Domain)
            WHERE dom.name IN $domains OR dom.name = 'general'
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
            """
            with self._driver.session(database=self._database) as session:
                res = session.run(q, tokenSurfaces=token_surfaces, domains=include_domains)
                return [record.data() for record in res]
        else:
            q = """
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
            """
            with self._driver.session(database=self._database) as session:
                res = session.run(q, tokenSurfaces=token_surfaces)
                return [record.data() for record in res]


    def run_cypher(self, cypher, params=None):
        """Generic read-only query helper."""
        with self._driver.session(database=self._database) as session:
            res = session.run(cypher, params or {})
            return [r.data() for r in res]
