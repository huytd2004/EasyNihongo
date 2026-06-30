"""
build_cue_mapping.py — Tạo SUPPORTED_BY cue edges (Sense → Lexeme).

Chiến lược rule-based (2 bước):
  Step 1: JMdict xref cues — dùng 'related' cross-references từ senses_raw.json
  Step 2: Domain hardcode seeds — với mỗi sense chuyên ngành, intersect
          DOMAIN_CUE_SEEDS[domain] với tập Lexeme surface thực tế đã có.

Đảm bảo mỗi Sense chuyên ngành có ≥ MIN_CUES_PER_SENSE cues.
Output: cue_mapping_raw.json
"""
import json
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

from config import (
    NEO4J_DIR, DOMAIN_CUE_SEEDS, MIN_CUES_PER_SENSE,
)


def build_cue_mapping(
    out_dir: Path = NEO4J_DIR,
) -> list[dict]:
    """
    Đọc lexemes_raw.json + senses_raw.json, tạo cue mapping.

    Returns:
        list[dict] mỗi phần tử: {"senseId": ..., "cueSurface": ...}
    """
    lex_path   = out_dir / "lexemes_raw.json"
    sense_path = out_dir / "senses_raw.json"

    if not lex_path.exists() or not sense_path.exists():
        raise FileNotFoundError(
            "Cần chạy extract_from_jmdict.py trước để có lexemes_raw.json / senses_raw.json"
        )

    with open(lex_path, encoding="utf-8") as f:
        lexemes: list[dict] = json.load(f)
    with open(sense_path, encoding="utf-8") as f:
        senses: list[dict] = json.load(f)

    # ── Build lookup sets ─────────────────────────────────────────────────────
    # Surface của tất cả Lexeme đã có (để validate cue)
    lexeme_surfaces: set[str] = {lex["surface"] for lex in lexemes}

    print(f"Lexeme surfaces available: {len(lexeme_surfaces):,}")
    print(f"Senses to process:         {len(senses):,}")

    # ── Step 1: Collect xref cues từ JMdict ──────────────────────────────────
    # xrefs là surface text → chỉ giữ nếu tồn tại trong lexeme_surfaces
    sense_to_cues: dict[str, set[str]] = defaultdict(set)

    for sense in tqdm(senses, desc="Step 1: xref cues", unit="sense"):
        sense_id   = sense["senseId"]
        lexeme_id  = sense["lexemeId"]
        domain_key = sense["domainKey"]

        # Bỏ qua general (không cần cue cho general)
        if domain_key == "general":
            continue

        for xref_surface in sense.get("xrefs", []):
            xref_surface = xref_surface.strip()
            if xref_surface and xref_surface in lexeme_surfaces:
                # Không tự trỏ vào chính mình
                own_surface = next(
                    (l["surface"] for l in lexemes if l["lexemeId"] == lexeme_id), None
                )
                if xref_surface != own_surface:
                    sense_to_cues[sense_id].add(xref_surface)

    xref_total = sum(len(v) for v in sense_to_cues.values())
    print(f"  xref cues collected: {xref_total:,}")

    # ── Step 2: Domain hardcode seeds ────────────────────────────────────────
    # Build reverse lookup: lexemeId → surface
    lexeme_id_to_surface: dict[str, str] = {
        l["lexemeId"]: l["surface"] for l in lexemes
    }

    for sense in tqdm(senses, desc="Step 2: domain seeds", unit="sense"):
        sense_id   = sense["senseId"]
        lexeme_id  = sense["lexemeId"]
        domain_key = sense["domainKey"]

        if domain_key == "general":
            continue

        own_surface = lexeme_id_to_surface.get(lexeme_id, "")
        seed_surfaces = DOMAIN_CUE_SEEDS.get(domain_key, [])

        for seed in seed_surfaces:
            if seed in lexeme_surfaces and seed != own_surface:
                sense_to_cues[sense_id].add(seed)

            # Dừng sớm nếu đã đủ
            if len(sense_to_cues[sense_id]) >= MIN_CUES_PER_SENSE * 3:
                break

    # ── Step 3: Finalize — đảm bảo minimum cue count ─────────────────────────
    # Lấy domain seed list đầy đủ để pad khi thiếu
    all_domain_seeds_by_domain: dict[str, list[str]] = {
        domain: [s for s in seeds if s in lexeme_surfaces]
        for domain, seeds in DOMAIN_CUE_SEEDS.items()
    }

    underserved = 0
    for sense in senses:
        sense_id   = sense["senseId"]
        domain_key = sense["domainKey"]

        if domain_key == "general":
            continue

        cue_count = len(sense_to_cues[sense_id])
        if cue_count < MIN_CUES_PER_SENSE:
            # Pad với domain seeds thêm từ cross-domain nếu cần
            own_surface = lexeme_id_to_surface.get(sense["lexemeId"], "")
            for fallback_domain, seeds in DOMAIN_CUE_SEEDS.items():
                for seed in seeds:
                    if seed in lexeme_surfaces and seed != own_surface:
                        sense_to_cues[sense_id].add(seed)
                    if len(sense_to_cues[sense_id]) >= MIN_CUES_PER_SENSE:
                        break
                if len(sense_to_cues[sense_id]) >= MIN_CUES_PER_SENSE:
                    break

            if len(sense_to_cues[sense_id]) < MIN_CUES_PER_SENSE:
                underserved += 1

    # ── Build output list ─────────────────────────────────────────────────────
    cue_mapping: list[dict] = []
    for sense_id, cue_surfaces in sense_to_cues.items():
        for surface in sorted(cue_surfaces):
            cue_mapping.append({
                "senseId":    sense_id,
                "cueSurface": surface,
            })

    # ── Stats ─────────────────────────────────────────────────────────────────
    specialized_senses = [s for s in senses if s["domainKey"] != "general"]
    covered = sum(1 for s in specialized_senses if s["senseId"] in sense_to_cues)
    avg_cues = (
        sum(len(v) for v in sense_to_cues.values()) / len(sense_to_cues)
        if sense_to_cues else 0
    )

    print(f"\n── Kết quả cue mapping ──")
    print(f"  Specialized senses:        {len(specialized_senses):,}")
    print(f"  Senses với ≥1 cue:         {covered:,}")
    print(f"  Senses còn thiếu cue:      {underserved:,}")
    print(f"  Total cue rows:            {len(cue_mapping):,}")
    print(f"  Average cues/sense:        {avg_cues:.1f}")

    # Save
    out_path = out_dir / "cue_mapping_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cue_mapping, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved: {out_path}")

    return cue_mapping


if __name__ == "__main__":
    build_cue_mapping()
