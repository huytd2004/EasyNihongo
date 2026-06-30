from collections import defaultdict

# Trọng số đơn giản hoá: chỉ dùng domain + cue
W_DOMAIN = 0.60  # domain match — tín hiệu chính
W_CUE    = 0.40  # cue match   — tín hiệu ngữ cảnh


class Ranker:
    def score(
        self,
        sense_row: dict,
        detected_domains: list[str],
        neighbor_surfaces: set[str],
    ) -> float:
        """
        Tính score cho một sense dựa trên domain và cue matching.

        Params:
            sense_row        : dict từ batch_query_by_surfaces
                               Cần có: 'domain' (str), 'cues' (list[str])
            detected_domains : list domain phát hiện in-memory từ văn bản
            neighbor_surfaces: set surface của tất cả token trong đoạn
        Returns:
            float trong [0.0, 1.0]
        """
        score = 0.0
        detected_domains_set = set(detected_domains)

        # --- Domain match (0.60) ---
        # Sense đúng domain → cộng toàn bộ W_DOMAIN
        if sense_row.get('domain') in detected_domains_set:
            score += W_DOMAIN

        # --- Cue match (0.40) ---
        # Tỉ lệ cue của sense xuất hiện trong các token lân cận
        cues = sense_row.get('cues') or []
        if cues:
            matched = sum(1 for c in cues if c in neighbor_surfaces)
            score += W_CUE * (matched / len(cues))

        return round(score, 4)

    def rank(
        self,
        graph_evidence: list[dict],
        detected_domains: list[str],
    ) -> tuple[list[dict], list[dict]]:
        """
        Rank tất cả sense từ graph evidence.

        Params:
            graph_evidence  : kết quả từ batch_query_by_surfaces
                              Mỗi row cần: token, reading, jlpt, glossVi, domain, cues[]
            detected_domains: list domain phát hiện in-memory

        Returns:
            ranked_senses  : list[{surface, top_sense, score, alternatives}]
            key_vocabulary : list[{surface, reading, jlpt, glossVi, domain}]
        """
        # Dùng toàn bộ token surface trong đoạn làm neighbor context cho cue matching
        neighbor_surfaces: set[str] = {row['token'] for row in graph_evidence}

        # Group sense theo token surface
        by_token: dict[str, list[dict]] = defaultdict(list)
        for row in graph_evidence:
            by_token[row['token']].append(row)

        ranked_senses: list[dict] = []
        key_vocabulary: list[dict] = []

        for surface, senses in by_token.items():
            # Tính score và sort giảm dần; tiebreak bằng thứ tự Neo4j trả về (stable sort)
            scored = sorted(
                [
                    {'sense': s, 'score': self.score(s, detected_domains, neighbor_surfaces)}
                    for s in senses
                ],
                key=lambda x: x['score'],
                reverse=True,
            )

            top      = scored[0]
            top_sense = top['sense']

            ranked_senses.append({
                'surface':      surface,
                'top_sense':    top_sense,
                'score':        top['score'],
                'alternatives': [s['sense'] for s in scored[1:3]],  # giữ 2 sense thay thế
            })

            # Key vocabulary: từ đáng chú ý = đa nghĩa HOẶC domain-specific
            # (jlpt không có trong Neo4j graph — chỉ tồn tại ở PostgreSQL)
            is_polysemy        = len(scored) >= 2 and scored[1]['score'] > 0
            is_domain_specific = top_sense.get('domain') in set(detected_domains)
            is_notable         = is_domain_specific or is_polysemy

            if is_notable:
                key_vocabulary.append({
                    'surface': surface,
                    'reading': top_sense.get('reading', ''),
                    'glossVi': top_sense.get('glossVi', ''),
                    'domain':  top_sense.get('domain'),
                    'score':   top['score'],
                })

        return ranked_senses, key_vocabulary
