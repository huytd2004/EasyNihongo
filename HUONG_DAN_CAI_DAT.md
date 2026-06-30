# HƯỚNG DẪN CÀI ĐẶT VÀ KHỞI CHẠY HỆ THỐNG AI TUTOR (DATN)

Tài liệu này hướng dẫn chi tiết cách cài đặt và vận hành hệ thống **AI Tutor** (Đồ án Tốt nghiệp). Hệ thống bao gồm 3 thành phần chính:
1. **Frontend**: Giao diện người dùng (Vite + Vue.js).
2. **Backend**: API Gateway & Business Logic Server (Spring Boot / Java 17).
3. **AI Pipeline**: Pipeline xử lý ngôn ngữ, GraphRAG và tích hợp mô hình ngôn ngữ lớn (Python FastAPI).

---

## 1. Yêu cầu Hệ thống tối thiểu

Để chạy được toàn bộ hệ thống, máy tính của bạn cần được cài đặt sẵn:
- **Hệ điều hành**: Linux (Ubuntu/Debian được khuyến nghị), macOS, hoặc Windows (WSL2).
- **Java Development Kit (JDK)**: Phiên bản 17 hoặc mới hơn.
- **Node.js**: Phiên bản 18.x hoặc mới hơn (kèm theo `npm`).
- **Python**: Phiên bản 3.10 hoặc mới hơn.
- **Cơ sở dữ liệu**:
  - **PostgreSQL**: Phiên bản 14 hoặc mới hơn.
  - **Neo4j**: Phiên bản 5.x hoặc mới hơn.

---

## 2. Chuẩn bị Cơ sở Dữ liệu

### 2.1. Cấu hình PostgreSQL
1. Khởi động dịch vụ PostgreSQL trên máy của bạn.
2. Tạo một cơ sở dữ liệu mới tên là `datn` bằng cách chạy lệnh SQL sau hoặc sử dụng pgAdmin / DBeaver:
   ```sql
   CREATE DATABASE datn;
   ```
3. Đảm bảo cấu hình tài khoản truy cập khớp với thông tin mặc định trong `backend/src/main/resources/application.yaml`:
   - **URL**: `jdbc:postgresql://localhost:5432/datn`
   - **Username**: `postgres`
   - **Password**: `123456`
   *(Nếu bạn có cấu hình tài khoản PostgreSQL khác, hãy chỉnh sửa lại các thông số này trong file `application.yaml`)*.
4. **Lưu ý**: Hệ thống sử dụng chế độ `hibernate.ddl-auto: update`, do đó bảng và cấu hình quan hệ (Schema) sẽ được tự động khởi tạo khi chạy Backend lần đầu tiên.

### 2.2. Cấu hình Neo4j (Cho tính năng GraphRAG Dịch chuyên ngành)
1. Khởi động dịch vụ Neo4j.
2. Tạo một cơ sở dữ liệu mới tên là `datn-graph` hoặc `specialized-graph` (mặc định trong code là `datn-graph` hoặc `specialized-graph`).
3. Đảm bảo tài khoản đăng nhập Neo4j khớp với cấu hình trong `ai/python_pipeline/.env`:
   - **URI**: `bolt://localhost:7687`
   - **Username**: `neo4j`
   - **Password**: `12345678`
   - **Database**: `datn-graph`
4. Để import dữ liệu từ điển và mối quan hệ Graph vào Neo4j, hãy chạy các script seed (xem mục 3).

---

## 3. Cài đặt và Khởi chạy AI Pipeline (Python FastAPI)

AI Pipeline đóng vai trò xử lý các yêu cầu liên quan đến GraphRAG, dịch thuật thuật ngữ chuyên ngành, Speech-to-Text (STT), Text-to-Speech (TTS), và sinh bài học/câu chuyện bằng AI.

1. Di chuyển vào thư mục `ai/python_pipeline`:
   ```bash
   cd ai/python_pipeline
   ```
2. Tạo môi trường ảo Python (`venv`):
   ```bash
   python3 -m venv .venv
   ```
3. Kích hoạt môi trường ảo:
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - **Windows**:
     ```cmd
     .venv\Scripts\activate
     ```
4. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Cấu hình các biến môi trường trong file `.env` tại thư mục này. File `.env` chứa các API Key dịch vụ như Google Gemini, Groq, Neo4j, v.v. (File `.env` mẫu đã được đính kèm sẵn trong mã nguồn).
6. Khởi chạy Server AI (chạy trên cổng `8001`):
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8001
   ```
   *Hoặc chạy trực tiếp bằng python:*
   ```bash
   python server.py
   ```

*(Tùy chọn) Chạy Seeding cho Neo4j:*
Nếu bạn cần khởi tạo đồ thị từ điển thuật ngữ chuyên ngành:
```bash
cd ../scripts/seed_neo4j
pip install -r requirements.txt
# Chạy script seeding (bỏ qua bước dịch EN->VI nếu muốn chạy nhanh)
python main.py --skip-translate
```

---

## 4. Cài đặt và Khởi chạy Backend (Spring Boot)

Backend xử lý toàn bộ logic lưu trữ tài khoản, flashcards học tập, chấm điểm theo thuật toán SM-2, quản lý lịch sử ôn tập và chuyển tiếp các tác vụ AI.

1. Di chuyển vào thư mục `backend`:
   ```bash
   cd backend
   ```
2. Sử dụng Maven Wrapper có sẵn trong mã nguồn để build dự án:
   ```bash
   ./mvnw clean package -DskipTests
   ```
   *(Thao tác này sẽ biên dịch mã nguồn và tạo ra file jar tại `target/backend-0.0.1-SNAPSHOT.jar`)*.
3. Khởi chạy ứng dụng Spring Boot:
   ```bash
   ./mvnw spring-boot:run
   ```
   Hoặc chạy trực tiếp file jar đã build:
   ```bash
   java -jar target/backend-0.0.1-SNAPSHOT.jar
   ```
   Backend sẽ được khởi chạy mặc định trên cổng `8080`.

---

## 5. Cài đặt và Khởi chạy Frontend (Vite + Vue.js)

Giao diện đồ họa tương tác thân thiện với người dùng, kết nối trực tiếp đến Spring Boot API.

1. Di chuyển vào thư mục `frontend`:
   ```bash
   cd frontend
   ```
2. Cài đặt các gói thư viện Node.js:
   ```bash
   npm install
   ```
3. Khởi chạy server phát triển (Development Server):
   ```bash
   npm run dev
   ```
   Giao diện sẽ chạy ở địa chỉ mặc định `http://localhost:5173`. Bạn chỉ cần mở trình duyệt web và truy cập địa chỉ này để bắt đầu sử dụng.
4. **Chương trình đóng gói sẵn (Production Build)**:
   - Thư mục `dist` trong thư mục `frontend` chứa các file tĩnh đã được tối ưu hóa sau khi biên dịch (`npm run build`).
   - Để kiểm thử nhanh phiên bản build sẵn mà không cần chạy Dev Server, bạn có thể chạy:
     ```bash
     npm run preview
     ```
     Phiên bản này có kích thước cực kỳ gọn nhẹ (chỉ khoảng 700KB) và có thể dễ dàng triển khai (deploy) trực tiếp lên bất kỳ Web Server nào (như Nginx, Apache, Caddy).

---

## 6. Hướng dẫn Sử dụng & Kiểm thử Nhanh
Sau khi khởi chạy thành công cả 3 thành phần (AI Server - cổng 8001, Backend - cổng 8080, Frontend - cổng 5173) và cấu hình đầy đủ database:
1. Truy cập `http://localhost:5173`.
2. Tạo tài khoản người dùng mới (đăng ký) hoặc đăng nhập với các tài khoản mặc định.
3. Hệ thống hỗ trợ:
   - **Học từ vựng**: Tạo các bộ Flashcard, học qua thuật toán lặp lại ngắt quãng SM-2.
   - **Học tương tác bằng giọng nói**: Luyện phát âm thông qua micro, nhận phân tích phát âm và nội dung sửa lỗi tức thì.
   - **Dịch thuật chuyên ngành**: Sử dụng ô dịch thuật để dịch tài liệu Anh - Việt tích hợp GraphRAG (Neo4j kết hợp LLM) để trích xuất nghĩa chuẩn xác nhất của thuật ngữ chuyên ngành.
   - **Sinh bài tập ôn tập tự động**: AI tự phân tích các từ bạn hay trả lời sai hoặc phát âm chưa tốt để tạo ra câu chuyện tiếng Nhật/Anh hoặc bài tập trắc nghiệm riêng biệt cho bạn ôn tập.
