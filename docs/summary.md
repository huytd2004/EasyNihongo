# DATN — Smart Japanese Learning System: Project Summary

**Cập nhật lần cuối:** 2026-06-07 (17:00)

**Scope:** Hệ thống học tiếng Nhật thông minh hoàn chỉnh bao gồm Spring Boot 4 backend, PostgreSQL DB, Vue 3 + Tailwind CSS v4 frontend và AI Layer (Python FastAPI + Neo4j GraphRAG + LLM pipeline) hỗ trợ Dịch thuật chuyên ngành, Ôn tập thông minh (Quiz & Story) và AI Tutor tương tác thoại.

**Thư mục tài liệu:** `docs/`

---

## Recent Updates (Tính đến 2026-06-07)

- **AI Review Pipeline:** Hoàn thành tích hợp luồng sinh Trắc nghiệm ôn tập (Review Quiz) và Câu chuyện tương tác (Review Story) kết hợp thông tin flashcards, cấp độ JLPT của người học và mẫu lỗi sai gần đây (Recent Mistakes). Xử lý robust lỗi LLM (Gemini 503) và trích xuất JSON bị phân mảnh.
- **AI Tutor Pipeline:** Triển khai tính năng hội thoại AI Tutor đa phương thức (hỗ trợ nhập text hoặc ghi âm giọng nói STT qua Whisper và sinh giọng nói phản hồi TTS). Tích hợp cơ chế tự động phát hiện ngữ cảnh giao tiếp (auto-scenario detection) dựa trên tần suất từ vựng mục tiêu và tính năng kiểm tra lỗi ngữ pháp bắt buộc.
- **Specialized Translation Pipeline:** Tối ưu hóa Sense Ranking trên đồ thị tri thức Neo4j bằng cách chuyển đổi từ phát hiện chủ đề cứng sang cơ chế bỏ phiếu tần suất (frequency-voting system) kết hợp SudachiPy (Mode B) để tách cụm từ ghép tiếng Nhật.
- **SRS & SM-2 Algorithm:** Chuẩn hóa thuật toán Spaced Repetition (SM-2) đồng bộ cả backend lẫn frontend, sửa các lỗi truy vấn card due (`findDueByDeckAndUser`), hiển thị thời gian ôn tập động trực tiếp trên các nút đánh giá của Study Session.
- **Frontend & Backend Integration:** Hoàn thành tích hợp đầy đủ giao diện người dùng cho các tính năng Tra cứu Từ điển/Kanji/Ngữ pháp nâng cao, Comments Threaded lồng nhau, Quản lý bộ thẻ Flashcard (Decks & Stats), Ôn tập Quiz/Story và Trò chuyện với AI Tutor.

---

## 0. Tổng quan kiến trúc hệ thống

```
                                  ┌──────────────────────────────────────────────────────────────┐
                                  │                     CLIENT (Browser)                        │
                                  │              Vue 3 + Tailwind CSS v4 + Pinia               │
                                  │                      localhost:5173                          │
                                  └────────────────────────┬─────────────────────────────────────┘
                                                           │
                                                           │ REST API (HTTP/JSON / FormData)
                                                           │ proxy /api, /auth → :8080
                                                           │
                                  ┌────────────────────────▼─────────────────────────────────────┐
                                  │                 BACKEND (Spring Boot 4)                      │
                                  │           JWT Auth · Business Service · JPA                  │
                                  │                      localhost:8080                          │
                                  └───────────┬───────────────────────────────┬──────────────────┘
                                              │                               │
                                              │ JDBC / JPA                    │ HTTP REST (FastAPI) :8001
                                              │ (PostgreSQL 16)               │ & Subprocess Exec (CLI)
                                              │                               │
                                  ┌───────────▼────────────┐        ┌─────────▼──────────────────┐
                                  │      PostgreSQL        │        │      AI Layer (Python)     │
                                  │      datn DB           │        │   FastAPI Server (:8001)   │
                                  │      :5432             │        │   LLM Pipeline / STT / TTS  │
                                  └────────────────────────┘        └──────────┬─────────────────┘
                                                                               │
                                                                               │ Neo4j Driver
                                                                      ┌────────▼─────────┐
                                                                      │      Neo4j       │
                                                                      │      :7687       │
                                                                      └──────────────────┘
```

**Mô hình giao tiếp giữa Backend và AI Layer:**
1. **AI Tutor & Review (FastAPI - Port 8001):** Spring Boot giao tiếp qua `RestAiAdapter` bằng cách gọi REST API đến FastAPI endpoint.
2. **GraphRAG Translation Pipeline (CLI Subprocess):** Backend khởi chạy script `python_pipeline.runner` dưới dạng một tiến trình hệ thống con (Subprocess) và nhận kết quả JSON trả ra từ luồng output tiêu chuẩn (`stdout`). Tên package `python_pipeline` là tên kỹ thuật còn lại trong mã nguồn; pipeline hiện tại không sử dụng thư viện LangGraph/StateGraph.

---

## 1. Tech Stack

| Tầng / Vai trò | Công nghệ chi tiết |
| :--- | :--- |
| **Backend** | Java 21, Spring Boot 4.0.5, Spring Security 6.4+, JJWT 0.12.6, Hibernate 7 |
| **Frontend** | Vue 3, Vite 8, Tailwind CSS v4, Pinia, Axios, @vueuse/core, HTML5 Audio API |
| **Database (Relational)**| PostgreSQL 16 (`datn` DB) |
| **Database (Graph)** | Neo4j Community Server (lưu trữ Lexeme - Sense - Domain Graph) |
| **AI Layer (Python)** | Python 3.10+, FastAPI, Uvicorn, LLM pipeline, Google Generative AI (Gemini 2.5 Flash / Gemini 1.5 Pro) |
| **Speech (STT / TTS)** | **STT:** OpenAI Whisper API / Local Whisper / Faster-Whisper. **TTS:** gTTS / Edge TTS / Mock TTS |
| **NLP (Japanese)** | SudachiPy (Mode B) + sudachidict-core (Tokenization phục vụ Graph Translation & AI Tutor) |
| **JDK (Runtime)** | JetBrains JDK 25 (bundled IntelliJ) |

---

## 2. Coding Style & Conventions

- **Nguyên tắc thiết kế:** Clean Code, SOLID, Single Responsibility (SRS tách biệt khỏi Flashcard nội dung).
- **Frontend:** Composition API, cú pháp `<script setup>`, quản lý state bằng Pinia, thiết kế giao diện theo triết lý "The Meditative Canvas" (Không có border 1px cứng, định hình layout qua tonal shift và shadow mờ).
- **Backend:** RESTful API chuẩn, phân tách Controller - Service - Repository.
- **AI Layer:** Pipeline tách biệt, kiểm soát ngoại lệ chặt chẽ, tối ưu hóa prompt trả về JSON thuần.

### Standard Response Envelope (tất cả API phải dùng)

```json
{
  "status": "success | error",
  "code": 200,
  "message": "Thông báo ngắn gọn",
  "data": {},
  "timestamp": "2026-06-07T10:00:00Z"
}
```

---

## 3. Backend — Package Structure

```
vn.hust.huy.backend/
├── model/
│   ├── entity/
│   │   ├── User.java                  → bảng: users (tài khoản hệ thống)
│   │   ├── UserProfile.java           → bảng: user_profiles (streak, points, target)
│   │   ├── RefreshToken.java          → bảng: app_refresh_tokens (quản lý phiên đăng nhập)
│   │   ├── DictionaryEntry.java       → bảng: dictionary_entries (từ vựng, kanji, ngữ pháp)
│   │   ├── EntryRelation.java         → bảng: entry_relations (Word-Kanji, Đồng nghĩa)
│   │   ├── Example.java               → bảng: examples (câu ví dụ đi kèm từ điển)
│   │   ├── FlashcardDeck.java         → bảng: flashcard_decks (bộ sưu tập thẻ học)
│   │   ├── Flashcard.java             │ bảng: flashcards (nội dung thẻ tự biên soạn)
│   │   ├── SrsDetail.java             │ bảng: srs_details (thông số SM-2: interval, ease, repetitions)
│   │   ├── ConversationSession.java   → bảng: conversation_sessions (phiên AI Tutor)
│   │   ├── LearningLog.java           → bảng: learning_logs (tin nhắn chi tiết trong phiên)
│   │   ├── TutorSessionResult.java    → bảng: tutor_session_results (kết quả tổng hợp, mistakes, vocab)
│   │   └── Comment.java               → bảng: comments (bình luận cộng đồng trên mục từ điển)
│   └── enums/
│       ├── Role.java                  (ADMIN, USER)
│       ├── JlptLevel.java             (N5, N4, N3, N2, N1)
│       ├── EntryType.java             (word, kanji, grammar)
│       └── FlashcardStatus.java       (new, learning, review)
├── dto/
│   ├── request/
│   │   ├── RegisterRequest.java / LoginRequest.java / RefreshRequest.java
│   │   ├── DictionaryRequest.java / FlashcardRequest.java
│   │   ├── TutorSessionRequest.java (thiết lập phiên AI) / MessageRequest.java (tin nhắn text/metadata)
│   │   └── ReviewQuizRequest.java (yêu cầu sinh quiz/story với deckId, level, recentMistakes)
│   └── response/
│       ├── ApiResponse.java (envelope chuẩn)
│       ├── AuthResponse.java / UserResponse.java
│       ├── DictionaryResponse.java / FlashcardResponse.java
│       ├── TutorSessionResponse.java / MessageResponse.java / TutorResultResponse.java
│       └── ReviewQuizResponse.java / ReviewStoryResponse.java (dữ liệu quiz/story sinh từ LLM)
├── repository/
│   ├── UserRepository.java / RefreshTokenRepository.java
│   ├── DictionaryEntryRepository.java (tách searchAll và searchByType để tránh lỗi PostgreSQL enum)
│   ├── FlashcardRepository.java (truy vấn card cần học / thẻ mới có sắp xếp)
│   ├── FlashcardDeckRepository.java / CommentRepository.java
│   └── TutorSessionResultRepository.java / ConversationSessionRepository.java / LearningLogRepository.java
├── security/
│   ├── JwtTokenProvider.java / JwtAuthenticationFilter.java
│   ├── CustomUserDetailsService.java / SecurityConfig.java
├── service/
│   ├── AuthService / UserService / DictionaryService / CommentService
│   ├── FlashcardDeckService / FlashcardService
│   ├── TranslateService (tích hợp subprocess CLI dịch GraphRAG)
│   ├── TutorService (điều phối phiên trò chuyện, gọi FastAPI và xử lý STT/TTS)
│   ├── ReviewService (điều phối sinh Quiz và Story qua API FastAPI)
│   ├── ai/
│   │   ├── AiAdapter.java / RestAiAdapter.java (REST client gọi AI layer)
│   │   ├── STTAdapter.java (nhận diện giọng nói từ file ghi âm)
│   │   └── TTSAdapter.java (sinh giọng nói tiếng Nhật)
│   └── media/
│       └── AudioStorageService.java (lưu trữ file âm thanh người học ghi âm hoặc AI nói)
├── controller/
│   ├── AuthController.java / UserController.java
│   ├── DictionaryController.java / CommentController.java
│   ├── FlashcardController.java / FlashcardDeckController.java
│   ├── TranslateController.java (/api/v1/translate/quick và /deep)
│   ├── TutorController.java (/api/v1/tutor/sessions/**)
│   └── ReviewController.java (/api/v1/review/quiz/generate và /story/generate)
└── exception/
    ├── ErrorCode.java / AppException.java / GlobalExceptionHandler.java
```

---

## 4. Frontend — Cấu trúc Vue 3 (src/)

```
frontend/src/
├── main.js                        ← Khởi tạo Vue app, Pinia và Router
├── App.vue                        ← Root component chính
├── assets/
│   └── main.css                   ← Hệ thống thiết kế (The Meditative Canvas, CSS variables)
├── services/
│   ├── api.js                     ← Axios instance + JWT interceptor tự động refresh token
│   ├── dictionary.js / comment.js
│   ├── flashcard.js / translate.js
│   ├── tutor.js                   ← API kết nối AI Tutor (create session, send message, finish)
│   └── review.js                  ← API sinh trắc nghiệm và truyện tương tác
├── stores/
│   └── auth.js                    ← Quản lý JWT Token & thông tin đăng nhập
├── router/
│   └── index.js                   ← Điều hướng trang + Route guards (Yêu cầu đăng nhập)
├── components/
│   ├── layout/
│   │   └── AppLayout.vue          ← Sidebar điều hướng chung
│   └── dictionary/
│       ├── SearchHeader.vue       ← Thanh tìm kiếm debounced gợi ý từ khóa
│       └── CommentSection.vue     ← Threaded comments component lồng nhau dùng chung
└── views/
    ├── auth/
    │   ├── LoginView.vue / RegisterView.vue
    ├── dashboard/
    │   └── DashboardView.vue      ← Màn hình chính thống kê học tập, streak
    ├── dictionary/
    │   ├── DictionaryView.vue     ← Tìm kiếm bento grid, suggest chips, thêm flashcard nhanh
    │   └── DictionaryDetailView.vue
    ├── flashcard/
    │   ├── FlashcardsView.vue     ← Quản lý bộ sưu tập Decks, xem thống kê thẻ học
    │   ├── StudyView.vue          ← Ôn tập flashcard dạng 3D card flip
    │   └── StudySessionView.vue   ← Ôn tập SM-2 tính toán khoảng cách ngày hiển thị động trên nút bấm
    ├── tutor/
    │   ├── TutorSetupView.vue     ← Cài đặt AI Tutor: chọn chủ đề (hoặc auto), từ vựng đích, JLPT level
    │   ├── TutorChatView.vue      ← Phòng chat giao tiếp thoại và chữ với AI Sakura-sensei, sửa lỗi ngữ pháp trực quan
    │   └── TutorResultView.vue    ← Báo cáo kết quả phiên học, thống kê số lỗi, từ vựng mới
    ├── review/
    │   ├── ReviewSetupView.vue    ← Màn hình cấu hình sinh bài ôn tập (chọn bộ thẻ, số câu, chủ đề)
    │   ├── ReviewQuizView.vue     ← Trắc nghiệm điền khuyết đa lựa chọn sinh động từ AI
    │   ├── ReviewStoryView.vue    ← Câu chuyện tương tác phân nhánh dạng Visual Novel, có câu hỏi lựa chọn hành động
    │   └── StoryResultScreen.vue  ← Điểm số và tóm tắt cốt truyện tương tác đã hoàn thành
    └── profile/
        └── ProfileView.vue        ← Thông tin người dùng, cài đặt mục tiêu học tập
```

---

## 5. Kiến trúc JWT Authentication

```
Client request
   │
   ▼
JwtAuthenticationFilter ──[Nếu không hợp lệ/hết hạn]──► Trả về 401 Unauthorized
   │
   ├──[Trích xuất Bearer Token & Validate]
   ▼
SecurityContextHolder (Set Authentication)
   │
   ▼
Controller Endpoint ──► Service ──► DB
```

- **Access Token:** Hết hạn sau 15 phút. Lưu trong memory/local state.
- **Refresh Token:** Hết hạn sau 7 ngày. Lưu trong DB (`app_refresh_tokens`) và `localStorage` của Client.
- **Cơ chế Auto-Refresh:** Khi một API request nhận lỗi `401 Unauthorized`, Axios interceptor tạm dừng các request khác, gửi request `POST /auth/refresh`, lưu Access Token mới và thử lại (retry) tất cả request bị lỗi trước đó mà không làm ngắt quãng trải nghiệm người dùng.

---

## 6. Danh sách API Endpoints

### 🔑 Authentication & Users
- `POST /auth/register` (Public): Đăng ký tài khoản mới kèm cấp độ mục tiêu JLPT.
- `POST /auth/login` (Public): Đăng nhập → Nhận Access Token + Refresh Token.
- `POST /auth/refresh` (Public): Đổi Refresh Token lấy Access Token mới.
- `POST /auth/logout` (Public): Xóa Refresh Token khỏi cơ sở dữ liệu.
- `GET /users/me` (Yêu cầu JWT): Lấy thông tin tài khoản và cấu hình profile hiện tại.

### 📖 Từ điển & Bình luận (Dictionary & Community)
- `GET /api/v1/dictionary` (Yêu cầu JWT): Tra cứu từ điển với tham số debounced `?q=...&type=word|kanji|grammar&page=0&size=N`.
- `GET /api/v1/dictionary/{id}` (Yêu cầu JWT): Xem chi tiết mục từ điển kèm quan hệ Kanji/Từ ghép thành phần và ví dụ.
- `POST /api/v1/dictionary` (Admin): Thêm mục từ điển mới.
- `PUT /api/v1/dictionary/{id}` (Admin): Cập nhật mục từ điển.
- `GET /api/v1/comments?entryId={id}` (Yêu cầu JWT): Lấy danh sách bình luận cấp cao (Top-level) của mục từ điển.
- `GET /api/v1/comments/{id}/replies` (Yêu cầu JWT): Lấy danh sách câu trả lời (replies) của một bình luận lồng nhau.
- `POST /api/v1/comments` (Yêu cầu JWT): Đăng bình luận hoặc câu trả lời mới (hỗ trợ `parentId`).
- `DELETE /api/v1/comments/{id}` (Yêu cầu JWT): Xóa bình luận (chỉ tác giả hoặc admin).

### 🗃️ Bộ thẻ Flashcard & Spaced Repetition (SRS)
- `GET /api/v1/decks` (Yêu cầu JWT): Danh sách các bộ thẻ (decks) kèm thống kê số lượng thẻ (New, Learning, Review).
- `POST /api/v1/decks` (Yêu cầu JWT): Tạo bộ thẻ mới.
- `PUT /api/v1/decks/{id}` (Yêu cầu JWT): Sửa thông tin bộ thẻ.
- `DELETE /api/v1/decks/{id}` (Yêu cầu JWT): Xóa bộ thẻ (xóa cascade toàn bộ thẻ thuộc bộ).
- `GET /api/v1/flashcards?deckId={id}` (Yêu cầu JWT): Lấy danh sách thẻ thuộc bộ chỉ định.
- `POST /api/v1/flashcards` (Yêu cầu JWT): Tạo thẻ học mới (Front, FrontReading, Back, BackNotes) và tự động khởi tạo SRS state.
- `PUT /api/v1/flashcards/{id}` (Yêu cầu JWT): Sửa đổi nội dung thẻ học.
- `PATCH /api/v1/flashcards/{id}/review` (Yêu cầu JWT): Gửi kết quả đánh giá thẻ theo thuật toán SM-2 (gồm rating: `again`, `hard`, `good`, `easy`).
- `DELETE /api/v1/flashcards/{id}` (Yêu cầu JWT): Xóa thẻ học.

### 🌐 Dịch thuật Chuyên ngành (Translation Layer)
- `POST /api/v1/translate/quick` (Yêu cầu JWT): Dịch nhanh thông qua Google Translate API công cộng.
- `POST /api/v1/translate/deep` (Yêu cầu JWT): Dịch phân tích sâu chuyên ngành sử dụng Neo4j GraphRAG và LLM pipeline. Trả về bản dịch chuẩn, danh sách thuật ngữ chuyên ngành phân tích nghĩa và ghi chú kỹ thuật.

### 🤖 Ôn tập Trí tuệ nhân tạo (AI Review Pipeline)
- `POST /api/v1/review/quiz/generate` (Yêu cầu JWT): Sinh danh sách câu hỏi trắc nghiệm JLPT từ danh sách từ vựng bộ thẻ học và mẫu lỗi sai gần đây.
- `POST /api/v1/review/story/generate` (Yêu cầu JWT): Sinh kịch bản cốt truyện tương tác phân nhánh lồng ghép câu hỏi ngữ cảnh dựa trên từ vựng cần ôn tập.

### 🗣️ Gia sư ảo giao tiếp (AI Tutor Pipeline)
- `POST /api/v1/tutor/sessions` (Yêu cầu JWT): Tạo một phiên học giao tiếp mới (nhận chủ đề, từ vựng mục tiêu, sinh tin nhắn chào hỏi ban đầu và file âm thanh đi kèm).
- `GET /api/v1/tutor/sessions/{id}` (Yêu cầu JWT): Xem thông tin cơ bản của phiên học.
- `POST /api/v1/tutor/sessions/{id}/messages` (Yêu cầu JWT): Gửi tin nhắn của người học (dạng chữ hoặc giọng nói). Thực hiện STT nếu có audio, chuyển đến AI Layer để sinh câu trả lời tiếng Nhật, dịch nghĩa Việt, bắt lỗi ngữ pháp và tạo âm thanh phản hồi.
- `PATCH /api/v1/tutor/sessions/{id}/finish` (Yêu cầu JWT): Kết thúc phiên trò chuyện, tính toán thời lượng, điểm chất lượng hội thoại (Fluency, Accuracy) và lưu trữ kết quả.
- `GET /api/v1/tutor/sessions/{id}/result` (Yêu cầu JWT): Nhận báo cáo chi tiết kết quả học tập của phiên.
- `GET /api/v1/tutor/sessions/results/recent` (Yêu cầu JWT): Lấy danh sách tổng hợp các lỗi ngữ pháp đã mắc gần đây để hiển thị ôn tập.
- `GET /api/v1/tutor/sessions/audio/{sessionId}/{filename}` (Public): Tải/Xem luồng (stream) file âm thanh giọng nói của phiên học.

---

## 7. Thiết kế Đồ thị Tri thức Neo4j & Thuật toán Dịch thuật

Hệ thống sử dụng cơ sở dữ liệu đồ thị Neo4j để giải quyết bài toán đa nghĩa của từ vựng tiếng Nhật trong các văn bản chuyên ngành thông qua cơ chế GraphRAG tĩnh.

### Node Types
- `Lexeme`: Đơn vị từ bề mặt (surface, reading, pos). Đóng vai trò là từ tra cứu hoặc từ gợi ý ngữ cảnh (cue).
- `Sense`: Nghĩa cụ thể của một Lexeme (glossVi, domain). Một Lexeme có thể trỏ đến nhiều Sense khác nhau.
- `Domain`: Miền chuyên ngành (medicine, technology, business, culture, academic, general).

### Relationships
- `(Lexeme) -[:HAS_SENSE]-> (Sense)`
- `(Sense) -[:BELONGS_TO]-> (Domain)`
- `(Sense) -[:SUPPORTED_BY]-> (Lexeme)`: Định nghĩa cue (từ vựng đồng xuất hiện) hỗ trợ nhận diện ngữ cảnh cho Sense đó.

### Thuật toán Bỏ phiếu Domain & Xếp hạng Nghĩa (Sense Ranking)
1. **Tokenization (SudachiPy Mode B):** Phân tích văn bản tiếng Nhật đầu vào thành các token đơn.
2. **Neo4j Pass 1:** Truy vấn tất cả senses của các token.
3. **Domain Vote:** Đếm số lượng từ xuất hiện thuộc từng miền chuyên ngành. Lựa chọn các domain có tỷ lệ vote vượt qua ngưỡng `30%` so với domain đứng đầu (bỏ qua domain `general` để tăng độ phân biệt).
4. **Neo4j Pass 2:** Lấy lại dữ liệu senses lọc theo các domain đã được phát hiện.
5. **Sense Scoring (In-Memory):**
   $$Score = 0.60 \times DomainMatch + 0.40 \times \left( \frac{\text{Số lượng Cue xuất hiện trong văn bản}}{\text{Tổng số Cue của Sense}} \right)$$
6. **Prompt Generation:** Đưa các nghĩa có điểm số cao nhất của các từ khóa quan trọng vào prompt của LLM làm ngữ cảnh để LLM sinh bản dịch chính xác nhất.

---

## 8. Thuật toán Lặp lại Ngắt quãng (SM-2 Spaced Repetition)

Hệ thống triển khai chuẩn hóa thuật toán SuperMemo-2 cho mô-đun Flashcards. Khi người học hoàn thành một thẻ học và đánh giá mức độ ghi nhớ (Rating):

- **Rating (Mức độ ghi nhớ):**
  - `0 (Again)`: Không nhớ gì cả.
  - `1 (Hard)`: Nhớ mang máng, mất nhiều thời gian nghĩ.
  - `2 (Good)`: Nhớ chính xác, phản xạ tốt.
  - `3 (Easy)`: Nhớ quá dễ dàng.

- **Công thức tính toán:**
  - **Repetitions (Số lần lặp lại thành công liên tiếp):**
    - Nếu Rating = `Again` (0) → reset `repetitions = 0`, thiết lập `interval_days = 1`.
    - Nếu Rating > `Again`: tăng `repetitions = repetitions + 1`.
  - **Ease Factor (Hệ số dễ học - EF):**
    - Công thức điều chỉnh EF dựa trên rating:
      $$EF_{new} = EF_{old} + (0.1 - (3 - Rating) \times (0.08 + (3 - Rating) \times 0.02))$$
    - EF tối thiểu được giới hạn là `1.3`.
  - **Interval Days (Khoảng cách ngày ôn tập tiếp theo):**
    - Nếu `repetitions = 1` → `interval = 1 ngày`.
    - Nếu `repetitions = 2` → `interval = 6 ngày`.
    - Nếu `repetitions > 2` → `interval = interval_{old} \times EF_{new}` (làm tròn lên số nguyên gần nhất).
  - **Next Review Date:**
    $$NextReview = CurrentTime + IntervalDays$$

---

## 9. Các vấn đề phát sinh & Cách giải quyết

### 1. Xung đột Enum kiểu dữ liệu giữa Hibernate và PostgreSQL
- **Vấn đề:** Khi tìm kiếm mục từ điển với JPQL có điều kiện loại mục từ `(:type IS NULL OR d.entryType = :type)`, Hibernate không thể gán giá trị `null` cho parameter có kiểu native enum của PostgreSQL, gây ra lỗi HTTP 500.
- **Giải quyết:** Tách thành hai phương thức truy vấn riêng biệt trong Repository: `searchAll(q, pageable)` (khi không lọc loại từ) và `searchByType(q, type, pageable)` (khi có lọc loại từ).

### 2. Dữ liệu rác gây sập luồng hiển thị mối quan hệ từ điển
- **Vấn đề:** Trong cơ sở dữ liệu có các quan hệ loại `antonym` nhưng trong enum `RelationType` của Java chưa khai báo giá trị này, dẫn tới Hibernate ném ngoại lệ và không thể load thông tin chi tiết từ vựng.
- **Giải quyết:** Thay đổi trường `relationType` trong Entity `EntryRelation` và DTO sang kiểu `String`. Enum `RelationType` chỉ giữ vai trò làm tài liệu tham khảo tĩnh.

### 3. Lỗi LLM không khả dụng (Gemini 503) & Phản hồi bị cắt cụt JSON
- **Vấn đề:** Khi sinh câu hỏi trắc nghiệm hoặc truyện tương tác với số lượng câu lớn, LLM đôi khi bị quá tải thời gian hoặc trả về JSON bị cắt ngang ở cuối, khiến parser của FastAPI bị lỗi.
- **Giải quyết:**
  - Viết parser tùy chỉnh sử dụng regex tham lam tìm kiếm khối `{...}` ngoài cùng, tự động vá các ký tự đóng ngoặc nhọn/ngoặc vuông bị thiếu cho chuỗi JSON bị cụt.
  - Triển khai cơ chế bắt lỗi lỗi dịch vụ AI (Gemini 503) từ FastAPI, trả về mã trạng thái HTTP 503 rõ ràng để Spring Boot backend nhận diện và xử lý fallback (tự sinh kịch bản mặc định hoặc hiển thị cảnh báo cho người học tải lại trang).

### 4. Lỗi Hibernate Alter Column enum của bảng Users gây treo ứng dụng lúc khởi động
- **Vấn đề:** Cột `role` trong DB là kiểu `varchar` nhưng Entity dùng `@JdbcTypeCode(SqlTypes.NAMED_ENUM)` trỏ tới `role_enum`. Hibernate cố gắng sửa kiểu dữ liệu của cột đang chứa dữ liệu cũ gây ra deadlock khóa bảng.
- **Giải quyết:** Tiến hành chạy migration thủ công bằng lệnh SQL để convert an toàn dữ liệu cột trước khi khởi động Spring Boot:
  ```sql
  ALTER TABLE users ALTER COLUMN role TYPE role_enum USING role::TEXT::role_enum;
  ```

---

## 10. Lệnh khởi chạy các dịch vụ

### Tầng AI (FastAPI Server)
Yêu cầu kích hoạt môi trường ảo Python và chạy uvicorn:
```bash
cd "/home/huutran/Documents/hoc tap/DATN/ai"
source python_pipeline/.venv/bin/activate
cd python_pipeline
python server.py
# Server chạy tại port 8001
```

### Tầng Backend (Spring Boot)
Thiết lập biến môi trường `JAVA_HOME` sử dụng JetBrains JBR và chạy maven wrapper:
```bash
export JAVA_HOME="/home/huutran/.local/share/JetBrains/Toolbox/apps/intellij-idea/jbr"
cd "/home/huutran/Documents/hoc tap/DATN/backend"
./mvnw spring-boot:run
# Server chạy tại port 8080
```

### Tầng Frontend (Vue 3 Dev Server)
```bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
cd "/home/huutran/Documents/hoc tap/DATN/frontend"
npm run dev
# Dev Server chạy tại: http://localhost:5173
```

---

## 11. Cơ sở dữ liệu & Cấu hình môi trường

### PostgreSQL (`backend/src/main/resources/application.yaml`)
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/datn
    username: postgres
    password: 123456
  jpa:
    hibernate:
      ddl-auto: update
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect

app:
  jwt:
    secret: 404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970
    access-token-expiration: 900000       # 15 phút
    refresh-token-expiration: 604800000     # 7 ngày
  tutor:
    ai-base-url: http://localhost:8001
    browser-tts: true                     # Bật phát âm trực tiếp trên browser
  translate:
    python-command: /home/huutran/Documents/hoc tap/DATN/ai/.venv/bin/python
    ai-root: /home/huutran/Documents/hoc tap/DATN/ai
```

### Script chạy khôi phục dữ liệu PostgreSQL mẫu
```bash
# Backup dữ liệu cũ
PGPASSWORD=123456 pg_dump -U postgres -h localhost datn > datn_backup.sql

# Thực thi file schema migration
PGPASSWORD=123456 psql -U postgres -h localhost -d datn -f crawl-data/migrate_schema.sql

# Import dữ liệu từ điển mẫu từ file JSON
cd crawl-data
python import_to_postgres.py --data-dir ./sample-data
```

---

## 12. Trạng thái Tiến độ Dự án (Project Progress Checklist)

### Tầng Backend
- [x] Schema normalization: Chuyển quyền sở hữu card từ user sang flashcard_decks.user_id.
- [x] Sửa câu lệnh SQL tìm card đến hạn `findDueByDeckAndUser` cho cả LEARNING và REVIEW.
- [x] Triển khai bộ API CRUD đầy đủ cho bộ thẻ `flashcard_decks` và thẻ `flashcards`.
- [x] Triển khai API bình luận threaded lồng nhau `comments` cho mục từ điển.
- [x] Triển khai API đánh giá thẻ `PATCH /api/v1/flashcards/{id}/review` theo SM-2.
- [x] Triển khai controller và service cho dịch thuật (`TranslateController` / `TranslateService`).
- [x] Triển khai controller và service cho ôn tập AI (`ReviewController` / `ReviewService`).
- [x] Triển khai controller và service cho trò chuyện thoại AI (`TutorController` / `TutorService`).
- [x] Quản lý lưu trữ tệp âm thanh ghi âm thoại của người học và âm thanh sinh ra từ AI.
- [ ] Mở rộng cơ sở dữ liệu từ điển đầy đủ từ tập crawl dữ liệu gốc (ngoài tập sample-data).
- [ ] Viết bộ Unit/Integration tests cho tầng Service và REST Controller.

### Tầng AI (Python Layer)
- [x] Cấu hình và chạy server FastAPI quản lý các request hội thoại và sinh ôn tập.
- [x] Phân tích ngữ nghĩa tiếng Nhật chuyên ngành (SudachiPy Mode B + Neo4j Pass 1 & 2).
- [x] Hiện thực thuật toán xếp hạng nghĩa từ vựng (Sense Ranking) in-memory.
- [x] Tích hợp Neo4j GraphRAG và LLM pipeline cho dịch thuật thuật ngữ chuyên ngành Nhật → Việt.
- [x] Triển khai generator sinh Quiz trắc nghiệm và Story câu chuyện tương tác từ vựng.
- [x] Tích hợp bộ chuyển giọng nói thành văn bản STT (Whisper API / Faster-Whisper local).
- [x] Tích hợp bộ chuyển văn bản thành giọng nói TTS phục vụ AI Tutor phát âm.
- [x] Triển khai prompt kiểm tra lỗi ngữ pháp bắt buộc cho mọi câu thoại của học sinh.

### Tầng Frontend (Vue 3 Client)
- [x] Cấu trúc khung dự án Vue 3 + Tailwind v4 + Pinia + Axios Interceptors.
- [x] Màn hình đăng nhập/đăng ký giao diện Meditative Canvas đồng bộ.
- [x] Bento Grid tra cứu Từ điển, Kanji và Ngữ pháp tích hợp bình luận cộng đồng thực tế.
- [x] Trình quản lý bộ thẻ Flashcards, hiển thị tiến trình và nút bấm ôn tập SM-2 tính khoảng cách ngày.
- [x] Màn hình ôn tập 3D card flip.
- [x] Màn hình ôn tập Trắc nghiệm sinh động từ AI (Review Quiz).
- [x] Màn hình ôn tập Câu chuyện tương tácVisual Novel (Review Story) kết nối backend.
- [x] Màn hình phòng chat AI Tutor (Tutor Chat) hỗ trợ thu âm ghi âm, gửi và phát âm thanh phản hồi từ AI.
- [x] Báo cáo chi tiết kết quả hội thoại AI Tutor (Tutor Result) sửa lỗi trực quan.
- [ ] Thiết kế responsive tối ưu hóa giao diện cho các thiết bị di động.
- [ ] Bổ sung hệ thống thông báo toast (Toast notifications) khi thao tác thành công/lỗi.
