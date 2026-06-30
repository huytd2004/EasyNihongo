import json
from pathlib import Path
from config import NEO4J_DIR
from generate_csvs import generate_csvs
from load_to_neo4j import load_to_neo4j

def main():
    print("--- Thêm thuật ngữ chuyên ngành vào Neo4j pipeline ---")

    # 1. Định nghĩa các Lexemes mới
    new_lexemes = [
        {"lexemeId": "lex_高負荷時", "surface": "高負荷時", "reading": "こうふかじ", "pos": "n", "jlpt": ""},
        {"lexemeId": "lex_タスク", "surface": "タスク", "reading": "たすく", "pos": "n", "jlpt": ""},
        {"lexemeId": "lex_処理", "surface": "処理", "reading": "しょり", "pos": "v", "jlpt": 3},
        {"lexemeId": "lex_スレッド", "surface": "スレッド", "reading": "すれっど", "pos": "n", "jlpt": ""},
        {"lexemeId": "lex_動的", "surface": "動的", "reading": "どうてき", "pos": "adj", "jlpt": ""},
        {"lexemeId": "lex_割り当てる", "surface": "割り当てる", "reading": "わりあてる", "pos": "v", "jlpt": 2},
        {"lexemeId": "lex_競合", "surface": "競合", "reading": "きょうごう", "pos": "v", "jlpt": ""},
        {"lexemeId": "lex_排他制御", "surface": "排他制御", "reading": "はいたせいぎょ", "pos": "n", "jlpt": ""}
    ]

    # Load & update lexemes_raw.json
    lex_path = NEO4J_DIR / "lexemes_raw.json"
    with open(lex_path, "r", encoding="utf-8") as f:
        lexemes = json.load(f)

    lex_added = 0
    for nl in new_lexemes:
        if not any(l["lexemeId"] == nl["lexemeId"] for l in lexemes):
            lexemes.append(nl)
            lex_added += 1
    
    if lex_added > 0:
        with open(lex_path, "w", encoding="utf-8") as f:
            json.dump(lexemes, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã thêm {lex_added} từ mới vào lexemes_raw.json")
    else:
        print("ℹ️ Các từ mới đã tồn tại trong lexemes_raw.json")

    # 2. Định nghĩa các Senses mới (senses_raw.json & senses_translated.json)
    # Senses cho các từ mới
    new_senses = [
        # 高負荷時
        {
            "senseId": "lex_高負荷時__general__0", "lexemeId": "lex_高負荷時",
            "glossEn": "at times of high load; heavy load period",
            "glossVi": "khi tải cao, thời gian tải nặng",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_高負荷時__technology__1", "lexemeId": "lex_高負荷時",
            "glossEn": "high load condition; system overload state",
            "glossVi": "lúc hệ thống chịu tải cao, quá tải hệ thống",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # タスク
        {
            "senseId": "lex_タスク__general__0", "lexemeId": "lex_タスク",
            "glossEn": "task; chore; duty",
            "glossVi": "nhiệm vụ, công việc",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_タスク__technology__1", "lexemeId": "lex_タスク",
            "glossEn": "task (execution unit); process; job",
            "glossVi": "tác vụ, nhiệm vụ xử lý",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # 処理
        {
            "senseId": "lex_処理__general__0", "lexemeId": "lex_処理",
            "glossEn": "processing; dealing with; treatment; disposal",
            "glossVi": "xử lý, giải quyết, thanh lý",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_処理__technology__1", "lexemeId": "lex_処理",
            "glossEn": "data processing; execution; transaction handling",
            "glossVi": "xử lý dữ liệu, thực thi tác vụ",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # スレッド
        {
            "senseId": "lex_スレッド__general__0", "lexemeId": "lex_スレッド",
            "glossEn": "thread (sewing); thread (message board, online forum)",
            "glossVi": "sợi chỉ, chủ đề thảo luận (trên diễn đàn)",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_スレッド__technology__1", "lexemeId": "lex_スレッド",
            "glossEn": "thread (computer science); execution thread",
            "glossVi": "luồng, luồng xử lý",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # プール (đã tồn tại lexeme, thêm sense mới)
        {
            "senseId": "lex_プール__technology__4", "lexemeId": "lex_プール",
            "glossEn": "pool (resource pool, thread pool)",
            "glossVi": "bể (luồng, tài nguyên)",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # 動的
        {
            "senseId": "lex_動的__general__0", "lexemeId": "lex_動的",
            "glossEn": "dynamic; active",
            "glossVi": "động, năng động",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_動的__technology__1", "lexemeId": "lex_動的",
            "glossEn": "dynamic (allocation, binding, compilation)",
            "glossVi": "động (cấp phát động, liên kết động)",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # 割り当てる
        {
            "senseId": "lex_割り当てる__general__0", "lexemeId": "lex_割り当てる",
            "glossEn": "to assign; to allot; to allocate",
            "glossVi": "phân công, phân chia, giao việc",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_割り当てる__technology__1", "lexemeId": "lex_割り当てる",
            "glossEn": "to allocate (memory, resources, threads)",
            "glossVi": "cấp phát (bộ nhớ, tài nguyên, luồng)",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # 競合
        {
            "senseId": "lex_競合__general__0", "lexemeId": "lex_競合",
            "glossEn": "competition; rivalry; conflict",
            "glossVi": "cạnh tranh, xung đột, thi đấu",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_競合__technology__1", "lexemeId": "lex_競合",
            "glossEn": "contention (thread, resource); conflict; race condition",
            "glossVi": "tranh chấp (luồng, tài nguyên), xung đột luồng",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        },
        # 排他制御
        {
            "senseId": "lex_排他制御__general__0", "lexemeId": "lex_排他制御",
            "glossEn": "exclusion control; restriction of others",
            "glossVi": "kiểm soát bài trừ, kiểm soát loại trừ",
            "domain": "domain_general", "domainKey": "general", "xrefs": []
        },
        {
            "senseId": "lex_排他制御__technology__1", "lexemeId": "lex_排他制御",
            "glossEn": "mutual exclusion; concurrency control; lock control",
            "glossVi": "kiểm soát loại trừ tương hỗ, xử lý loại trừ, đồng bộ hóa luồng",
            "domain": "domain_technology", "domainKey": "technology", "xrefs": []
        }
    ]

    # Update senses_raw.json
    senses_raw_path = NEO4J_DIR / "senses_raw.json"
    with open(senses_raw_path, "r", encoding="utf-8") as f:
        senses_raw = json.load(f)

    senses_raw_added = 0
    for ns in new_senses:
        if not any(s["senseId"] == ns["senseId"] for s in senses_raw):
            # Với senses_raw thì glossVi để trống
            ns_raw = ns.copy()
            ns_raw["glossVi"] = ""
            senses_raw.append(ns_raw)
            senses_raw_added += 1

    if senses_raw_added > 0:
        with open(senses_raw_path, "w", encoding="utf-8") as f:
            json.dump(senses_raw, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã thêm {senses_raw_added} senses vào senses_raw.json")
    else:
        print("ℹ️ Các senses đã tồn tại trong senses_raw.json")

    # Update senses_translated.json
    senses_trans_path = NEO4J_DIR / "senses_translated.json"
    with open(senses_trans_path, "r", encoding="utf-8") as f:
        senses_trans = json.load(f)

    senses_trans_added = 0
    for ns in new_senses:
        if not any(s["senseId"] == ns["senseId"] for s in senses_trans):
            senses_trans.append(ns)
            senses_trans_added += 1

    if senses_trans_added > 0:
        with open(senses_trans_path, "w", encoding="utf-8") as f:
            json.dump(senses_trans, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã thêm {senses_trans_added} senses vào senses_translated.json")
    else:
        print("ℹ️ Các senses đã tồn tại trong senses_translated.json")

    # 3. Định nghĩa các Cues mới cho các technology senses
    new_cues = {
        "lex_高負荷時__technology__1": ['システム', 'サーバー', 'タスク', '処理', 'スレッド', 'データベース'],
        "lex_タスク__technology__1": ['処理', 'スレッド', 'システム', '実行', '割り当て', 'キュー'],
        "lex_処理__technology__1": ['データ', 'タスク', 'スレッド', 'システム', '実行', '初期化', '例外'],
        "lex_スレッド__technology__1": ['プロセス', 'プール', '処理', 'タスク', '競合', '排他制御', '実行', '割り当て'],
        "lex_プール__technology__4": ['スレッド', '割り当て', '接続', '管理', '動的'],
        "lex_動的__technology__1": ['割り当て', 'メモリ', '生成', 'プログラム', '処理'],
        "lex_割り当てる__technology__1": ['メモリ', 'スレッド', 'プール', 'アドレス', '動的'],
        "lex_競合__technology__1": ['スレッド', '排他制御', 'アクセス', '処理', 'データベース'],
        "lex_排他制御__technology__1": ['スレッド', '競合', 'アクセス', 'ロック', '処理']
    }

    # Load & update cue_mapping_raw.json
    cue_path = NEO4J_DIR / "cue_mapping_raw.json"
    with open(cue_path, "r", encoding="utf-8") as f:
        cue_mapping = json.load(f)

    cues_added = 0
    for sense_id, cue_list in new_cues.items():
        for cue_surf in cue_list:
            exists = any(c["senseId"] == sense_id and c["cueSurface"] == cue_surf for c in cue_mapping)
            if not exists:
                cue_mapping.append({
                    "senseId": sense_id,
                    "cueSurface": cue_surf
                })
                cues_added += 1

    if cues_added > 0:
        with open(cue_path, "w", encoding="utf-8") as f:
            json.dump(cue_mapping, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã thêm {cues_added} cues vào cue_mapping_raw.json")
    else:
        print("ℹ️ Các cues đã tồn tại trong cue_mapping_raw.json")

    # 4. Tái tạo các file CSV
    print("\n--- Đang tái tạo các file CSV ---")
    generate_csvs(out_dir=NEO4J_DIR)

    # 5. Tải dữ liệu vào Neo4j
    print("\n--- Đang tải dữ liệu vào Neo4j ---")
    load_to_neo4j(data_dir=NEO4J_DIR)

if __name__ == "__main__":
    main()
