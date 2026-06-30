#!/bin/bash
# download_sources.sh — Tải toàn bộ raw data cần thiết cho pipeline
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data/raw"
mkdir -p "$DATA_DIR"

echo "============================================"
echo " Dictionary Data Pipeline — Download Script"
echo "============================================"
echo "Data sẽ được lưu vào: $DATA_DIR"
echo ""

# Lấy URL của release mới nhất từ GitHub API
echo "Đang lấy URL release mới nhất từ GitHub..."
RELEASE_JSON=$(curl -s "https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest")
RELEASE_TAG=$(echo "$RELEASE_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])")
echo "Sử dụng release: $RELEASE_TAG"

# Encode tag cho URL (+ → %2B)
RELEASE_TAG_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$RELEASE_TAG', safe=''))")

BASE_URL="https://github.com/scriptin/jmdict-simplified/releases/download/${RELEASE_TAG_ENC}"

# ─────────────────────────────────────────────────────────────
# 1. JMdict English JSON (jmdict-eng — chứa gloss tiếng Anh)
#    Dùng bản "-eng" (chỉ tiếng Anh, nhỏ hơn "-all")
# ─────────────────────────────────────────────────────────────
JMDICT_JSON="$DATA_DIR/jmdict-eng.json"

if [ ! -f "$JMDICT_JSON" ]; then
    echo "[1/4] Đang tải JMdict English JSON..."
    JMDICT_ZIP="$DATA_DIR/jmdict-eng.json.zip"
    curl -L --progress-bar \
        "${BASE_URL}/jmdict-eng-${RELEASE_TAG}.json.zip" \
        -o "$JMDICT_ZIP"
    echo "      Đang giải nén..."
    unzip -o "$JMDICT_ZIP" -d "$DATA_DIR/"
    # Rename về tên chuẩn
    find "$DATA_DIR" -name "jmdict-eng-*.json" ! -name "jmdict-eng.json" -exec mv {} "$JMDICT_JSON" \; 2>/dev/null || true
    echo "      ✅ JMdict done."
else
    echo "[1/4] ✅ JMdict đã tồn tại, bỏ qua."
fi

# ─────────────────────────────────────────────────────────────
# 2. Kanjidic2 English JSON (đã parse sẵn thành JSON)
#    Không cần parse XML gốc nữa
# ─────────────────────────────────────────────────────────────
KANJIDIC_JSON="$DATA_DIR/kanjidic2-en.json"

if [ ! -f "$KANJIDIC_JSON" ]; then
    echo "[2/4] Đang tải Kanjidic2 English JSON..."
    KANJIDIC_ZIP="$DATA_DIR/kanjidic2-en.json.zip"
    curl -L --progress-bar \
        "${BASE_URL}/kanjidic2-en-${RELEASE_TAG}.json.zip" \
        -o "$KANJIDIC_ZIP"
    echo "      Đang giải nén..."
    unzip -o "$KANJIDIC_ZIP" -d "$DATA_DIR/"
    find "$DATA_DIR" -name "kanjidic2-en-*.json" ! -name "kanjidic2-en.json" -exec mv {} "$KANJIDIC_JSON" \; 2>/dev/null || true
    echo "      ✅ Kanjidic2 JSON done."
else
    echo "[2/4] ✅ Kanjidic2 JSON đã tồn tại, bỏ qua."
fi

# ─────────────────────────────────────────────────────────────
# 3. KradFile JSON (kanji → radicals mapping, đã parse sẵn)
#    Không cần deal với encoding EUC-JP
# ─────────────────────────────────────────────────────────────
KRADFILE_JSON="$DATA_DIR/kradfile.json"

if [ ! -f "$KRADFILE_JSON" ]; then
    echo "[3/4] Đang tải KradFile JSON (radical mapping)..."
    KRADFILE_ZIP="$DATA_DIR/kradfile.json.zip"
    curl -L --progress-bar \
        "${BASE_URL}/kradfile-${RELEASE_TAG}.json.zip" \
        -o "$KRADFILE_ZIP"
    echo "      Đang giải nén..."
    unzip -o "$KRADFILE_ZIP" -d "$DATA_DIR/"
    find "$DATA_DIR" -name "kradfile-*.json" ! -name "kradfile.json" -exec mv {} "$KRADFILE_JSON" \; 2>/dev/null || true
    echo "      ✅ KradFile JSON done."
else
    echo "[3/4] ✅ KradFile JSON đã tồn tại, bỏ qua."
fi

# ─────────────────────────────────────────────────────────────
# 4. Tatoeba Sentences + Links
#    Từ: https://tatoeba.org/en/downloads
# ─────────────────────────────────────────────────────────────
SENTENCES_CSV="$DATA_DIR/sentences.csv"
LINKS_CSV="$DATA_DIR/links.csv"

if [ ! -f "$SENTENCES_CSV" ]; then
    echo "[4/4] Đang tải Tatoeba sentences (~900MB, có thể mất vài phút)..."
    curl --progress-bar \
        "https://downloads.tatoeba.org/exports/sentences.tar.bz2" \
        -o "$DATA_DIR/sentences.tar.bz2"
    echo "      Đang giải nén sentences..."
    tar -xjf "$DATA_DIR/sentences.tar.bz2" -C "$DATA_DIR/"
    echo "      ✅ Tatoeba sentences done."
else
    echo "[4/4] ✅ Tatoeba sentences đã tồn tại, bỏ qua."
fi

if [ ! -f "$LINKS_CSV" ]; then
    echo "      Đang tải Tatoeba links..."
    curl --progress-bar \
        "https://downloads.tatoeba.org/exports/links.tar.bz2" \
        -o "$DATA_DIR/links.tar.bz2"
    echo "      Đang giải nén links..."
    tar -xjf "$DATA_DIR/links.tar.bz2" -C "$DATA_DIR/"
    echo "      ✅ Tatoeba links done."
else
    echo "      ✅ Tatoeba links đã tồn tại, bỏ qua."
fi

echo ""
echo "============================================"
echo " ✅ Tải xong! Các file trong $DATA_DIR:"
ls -lh "$DATA_DIR/"
echo "============================================"
