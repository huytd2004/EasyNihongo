#!/bin/bash

# Script khởi chạy đồng thời 3 thành phần của hệ thống AI Tutor

# Màu sắc hiển thị
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0;0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}      HỆ THỐNG AI TUTOR (ĐỒ ÁN TỐT NGHIỆP) - RUNNER SCRIPT      ${NC}"
echo -e "${BLUE}================================================================${NC}"

# Hàm xử lý khi tắt script (Ctrl+C)
cleanup() {
    echo -e "\n${YELLOW}Đang dừng tất cả các server...${NC}"
    kill $AI_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Đã tắt tất cả các thành phần. Tạm biệt!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 1. Khởi chạy AI Pipeline (Python FastAPI)
echo -e "\n${BLUE}[1/3] Khởi chạy Python AI Pipeline (FastAPI)...${NC}"
if [ -d "ai/python_pipeline/.venv" ]; then
    source ai/python_pipeline/.venv/bin/activate
    cd ai/python_pipeline
    uvicorn server:app --host 0.0.0.0 --port 8001 > server.log 2>&1 &
    AI_PID=$!
    cd ../..
    echo -e "${GREEN} -> FastAPI Server đang khởi chạy ở nền (PID: $AI_PID, Port: 8001). Log lưu tại ai/python_pipeline/server.log${NC}"
else
    echo -e "${RED} [LỖI] Không tìm thấy thư mục môi trường ảo Python: ai/python_pipeline/.venv${NC}"
    echo -e "${YELLOW} Vui lòng thiết lập môi trường Python trước theo file HUONG_DAN_CAI_DAT.md${NC}"
fi

# 2. Khởi chạy Backend (Spring Boot)
echo -e "\n${BLUE}[2/3] Khởi chạy Spring Boot Backend...${NC}"
if [ -f "backend/pom.xml" ]; then
    cd backend
    ./mvnw spring-boot:run > backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN} -> Spring Boot đang khởi chạy ở nền (PID: $BACKEND_PID, Port: 8080). Log lưu tại backend/backend.log${NC}"
else
    echo -e "${RED} [LỖI] Không tìm thấy dự án Spring Boot tại thư mục backend/${NC}"
fi

# 3. Khởi chạy Frontend (Vite + Vue)
echo -e "\n${BLUE}[3/3] Khởi chạy Frontend (Vite + Vue)...${NC}"
if [ -d "frontend/node_modules" ]; then
    cd frontend
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN} -> Vite Dev Server đang khởi chạy ở nền (PID: $FRONTEND_PID, Port: 5173). Log lưu tại frontend/frontend.log${NC}"
else
    echo -e "${RED} [LỖI] Chưa cài đặt node_modules cho frontend.${NC}"
    echo -e "${YELLOW} Vui lòng cd vào frontend và chạy 'npm install' trước.${NC}"
fi

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}Hệ thống đang chạy! Hãy mở trình duyệt truy cập: http://localhost:5173${NC}"
echo -e "${YELLOW}Bấm Ctrl+C để dừng tất cả các server cùng lúc.${NC}"
echo -e "${BLUE}================================================================${NC}"

# Giữ script hoạt động để hứng tín hiệu Ctrl+C
while true; do
    sleep 1
done
