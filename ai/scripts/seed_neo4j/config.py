"""
config.py — Cấu hình chung cho Neo4j seeding pipeline.

Bao gồm:
- Kết nối Neo4j
- Mapping JMdict misc tags → domain
- Domain cue hardcode (rule-based)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j Connection ──────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")  # Default: neo4j (system db)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
RAW_DIR         = DATA_DIR / "raw"
NEO4J_DIR       = DATA_DIR / "neo4j"
JMDICT_JSON     = BASE_DIR.parent / "seed_dictionary" / "data" / "raw" / "jmdict-eng.json"
TRANS_CACHE     = DATA_DIR / "translation_cache_neo4j.json"

# ── Domain definitions ────────────────────────────────────────────────────────
DOMAINS = {
    "technology": "Công nghệ / Kỹ thuật",
    "medicine":   "Y học / Sinh học",
    "academic":   "Học thuật / Khoa học",
    "business":   "Kinh doanh / Kinh tế",
    "culture":    "Văn hóa / Nghệ thuật",
    "general":    "Phổ thông",
}

# ── JMdict misc → domain mapping ──────────────────────────────────────────────
# Tham chiếu: https://www.edrdg.org/jmwsgi/edhelp.py?svc=jmdict&sid=#fielddt
MISC_TO_DOMAIN: dict[str, str] = {
    # Technology
    "comp":    "technology",
    "tech":    "technology",
    "elec":    "technology",
    "engr":    "technology",
    "telec":   "technology",
    "mach":    "technology",
    "internet":"technology",
    "vidg":    "technology",
    "photo":   "technology",
    "print":   "technology",
    # Medicine
    "med":     "medicine",
    "anat":    "medicine",
    "biol":    "medicine",
    "pharm":   "medicine",
    "dent":    "medicine",
    "surg":    "medicine",
    "psych":   "medicine",
    "psy":     "medicine",
    "physiol": "medicine",
    "biochem": "medicine",
    "genet":   "medicine",
    "zool":    "medicine",
    "bot":     "medicine",
    # Academic
    "math":    "academic",
    "physics": "academic",
    "chem":    "academic",
    "astron":  "academic",
    "geol":    "academic",
    "ling":    "academic",
    "phil":    "academic",
    "law":     "academic",
    "logic":   "academic",
    "gramm":   "academic",
    "min":     "academic",
    # Business
    "bus":     "business",
    "econ":    "business",
    "finc":    "business",
    "acctg":   "business",
    "pol":     "business",
    "mil":     "business",
    "tradem":  "business",
    # Culture
    "music":   "culture",
    "art":     "culture",
    "food":    "culture",
    "sports":  "culture",
    "archit":  "culture",
    "cloth":   "culture",
    "Buddh":   "culture",
    "Shinto":  "culture",
    "Christn": "culture",
    "MA":      "culture",
    "baseb":   "culture",
    "sumo":    "culture",
    "go":      "culture",
    "shogi":   "culture",
    "mahj":    "culture",
    "golf":    "culture",
    "cards":   "culture",
    "hanaf":   "culture",
}

# ── Hardcode cue seeds per domain ─────────────────────────────────────────────
# Rule-based: mỗi domain có một tập surface tokens điển hình.
# build_cue_mapping.py sẽ intersect với Lexeme surface thực tế đã có.
DOMAIN_CUE_SEEDS: dict[str, list[str]] = {
    "technology": [
        "システム", "データ", "ネットワーク", "プログラム", "ソフトウェア",
        "ハードウェア", "デジタル", "製造", "プロセス", "半導体",
        "回路", "電子", "機械", "自動", "制御",
        "通信", "インターネット", "開発", "設計", "アルゴリズム",
        "データベース", "サーバー", "クラウド", "処理", "演算",
    ],
    "medicine": [
        "患者", "治療", "診断", "手術", "病院",
        "薬", "症状", "感染", "血液", "細胞",
        "遺伝子", "免疫", "神経", "心臓", "脳",
        "骨", "筋肉", "肝臓", "腎臓", "肺",
        "検査", "医師", "看護", "臨床", "投薬",
    ],
    "academic": [
        "研究", "理論", "実験", "分析", "計算",
        "方程式", "証明", "仮説", "観測", "データ",
        "統計", "論文", "学術", "科学", "物理",
        "化学", "生物", "数学", "哲学", "言語",
        "大学", "教授", "博士", "学術", "調査",
    ],
    "business": [
        "会社", "市場", "利益", "投資", "経済",
        "契約", "取引", "顧客", "販売", "管理",
        "戦略", "競争", "予算", "財務", "株式",
        "銀行", "貿易", "輸出", "輸入", "価格",
        "マーケット", "ビジネス", "企業", "経営", "収益",
    ],
    "culture": [
        "音楽", "芸術", "文化", "伝統", "歴史",
        "映画", "演劇", "絵画", "彫刻", "建築",
        "料理", "食文化", "スポーツ", "武道", "茶道",
        "花道", "着物", "祭り", "神社", "寺",
        "文学", "詩", "宗教", "儀式", "礼儀",
    ],
    "general": [
        "人", "時間", "場所", "方法", "理由",
        "問題", "結果", "影響", "変化", "関係",
    ],
}

# ── Polysemy filter ───────────────────────────────────────────────────────────
# Lexeme phải có ít nhất MIN_SENSES_FOR_POLYSEMY sense (bất kỳ domain)
# VÀ ít nhất 1 sense có domain != general
MIN_SENSES_FOR_POLYSEMY = 2
MIN_CUES_PER_SENSE = 5   # Tiêu chuẩn theo schema-neo4j.md §6
