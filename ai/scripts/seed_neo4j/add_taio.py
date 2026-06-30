import json
import os
from pathlib import Path
from config import NEO4J_DIR
from generate_csvs import generate_csvs
from load_to_neo4j import load_to_neo4j

def main():
    print("--- Thêm từ '対応' (nghĩa là 'xử lý') vào Neo4j pipeline ---")

    # 1. Update lexemes_raw.json
    lex_path = NEO4J_DIR / "lexemes_raw.json"
    if lex_path.exists():
        with open(lex_path, "r", encoding="utf-8") as f:
            lexemes = json.load(f)
    else:
        lexemes = []

    # Check if 'lex_対応' already exists
    lexeme_exists = any(l["lexemeId"] == "lex_対応" for l in lexemes)
    if not lexeme_exists:
        new_lexeme = {
            "lexemeId": "lex_対応",
            "surface": "対応",
            "reading": "たいおう",
            "pos": "v",
            "jlpt": 3
        }
        lexemes.append(new_lexeme)
        with open(lex_path, "w", encoding="utf-8") as f:
            json.dump(lexemes, f, ensure_ascii=False, indent=2)
        print("✅ Đã thêm '対応' vào lexemes_raw.json")
    else:
        print("ℹ️ '対応' đã tồn tại trong lexemes_raw.json")

    # 2. Update senses_raw.json
    senses_raw_path = NEO4J_DIR / "senses_raw.json"
    if senses_raw_path.exists():
        with open(senses_raw_path, "r", encoding="utf-8") as f:
            senses_raw = json.load(f)
    else:
        senses_raw = []

    s1_exists = any(s["senseId"] == "lex_対応__general__0" for s in senses_raw)
    s2_exists = any(s["senseId"] == "lex_対応__technology__1" for s in senses_raw)

    if not s1_exists:
        senses_raw.append({
            "senseId": "lex_対応__general__0",
            "lexemeId": "lex_対応",
            "glossEn": "interaction; correspondence; coping; dealing; adaptation; response",
            "glossVi": "",
            "domain": "domain_general",
            "domainKey": "general",
            "xrefs": []
        })
    if not s2_exists:
        senses_raw.append({
            "senseId": "lex_対応__technology__1",
            "lexemeId": "lex_対応",
            "glossEn": "handling; processing; support; coping with",
            "glossVi": "",
            "domain": "domain_technology",
            "domainKey": "technology",
            "xrefs": []
        })

    if not (s1_exists and s2_exists):
        with open(senses_raw_path, "w", encoding="utf-8") as f:
            json.dump(senses_raw, f, ensure_ascii=False, indent=2)
        print("✅ Đã thêm các senses vào senses_raw.json")
    else:
        print("ℹ️ Các senses đã tồn tại trong senses_raw.json")

    # 3. Update senses_translated.json
    senses_trans_path = NEO4J_DIR / "senses_translated.json"
    if senses_trans_path.exists():
        with open(senses_trans_path, "r", encoding="utf-8") as f:
            senses_trans = json.load(f)
    else:
        senses_trans = []

    s1_trans_exists = any(s["senseId"] == "lex_対応__general__0" for s in senses_trans)
    s2_trans_exists = any(s["senseId"] == "lex_対応__technology__1" for s in senses_trans)

    if not s1_trans_exists:
        senses_trans.append({
            "senseId": "lex_対応__general__0",
            "lexemeId": "lex_対応",
            "glossEn": "interaction; correspondence; coping; dealing; adaptation; response",
            "glossVi": "đối ứng, đáp ứng, thích ứng, tương thích, phù hợp",
            "domain": "domain_general",
            "domainKey": "general",
            "xrefs": []
        })
    if not s2_trans_exists:
        senses_trans.append({
            "senseId": "lex_対応__technology__1",
            "lexemeId": "lex_対応",
            "glossEn": "handling; processing; support; coping with",
            "glossVi": "xử lý, giải quyết, hỗ trợ",
            "domain": "domain_technology",
            "domainKey": "technology",
            "xrefs": []
        })

    if not (s1_trans_exists and s2_trans_exists):
        with open(senses_trans_path, "w", encoding="utf-8") as f:
            json.dump(senses_trans, f, ensure_ascii=False, indent=2)
        print("✅ Đã thêm các senses vào senses_translated.json")
    else:
        print("ℹ️ Các senses đã tồn tại trong senses_translated.json")

    # 4. Update cue_mapping_raw.json
    cue_path = NEO4J_DIR / "cue_mapping_raw.json"
    if cue_path.exists():
        with open(cue_path, "r", encoding="utf-8") as f:
            cue_mapping = json.load(f)
    else:
        cue_mapping = []

    # Cues for technology sense (lex_対応__technology__1)
    tech_cues = ['アクセス', 'アドレス', 'アプリケーション', 'イメージ', 'インポート', 'ウィンドウ', 'ウィザード', 'エラー', 'サーバー', '初期化']
    cues_added = 0
    for cue_surf in tech_cues:
        exists = any(c["senseId"] == "lex_対応__technology__1" and c["cueSurface"] == cue_surf for c in cue_mapping)
        if not exists:
            cue_mapping.append({
                "senseId": "lex_対応__technology__1",
                "cueSurface": cue_surf
            })
            cues_added += 1

    if cues_added > 0:
        with open(cue_path, "w", encoding="utf-8") as f:
            json.dump(cue_mapping, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã thêm {cues_added} cues cho technology sense vào cue_mapping_raw.json")
    else:
        print("ℹ️ Cues cho technology sense đã tồn tại trong cue_mapping_raw.json")

    # 5. Regenerate CSVs
    print("\n--- Đang tái tạo các file CSV ---")
    generate_csvs(out_dir=NEO4J_DIR)

    # 6. Load to Neo4j
    print("\n--- Đang tải dữ liệu vào Neo4j ---")
    load_to_neo4j(data_dir=NEO4J_DIR)

if __name__ == "__main__":
    main()
