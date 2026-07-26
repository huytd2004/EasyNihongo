# Hướng dẫn Thiết lập CI/CD cơ bản cho Docker + VPS bằng GitHub Actions

Tài liệu này hướng dẫn bạn cách thiết lập quy trình tự động hóa tích hợp và triển khai liên tục (CI/CD) cho ứng dụng **AI Tutor** của bạn bằng **GitHub Actions** theo **Phương án 2 (Build & Push Docker Image)**.

Khi có mã nguồn mới được push lên nhánh chính (ví dụ: `main`), GitHub Actions sẽ tự động build các Docker image, push lên GitHub Packages (GHCR), và SSH vào VPS để tải về rồi restart hệ thống.

---

## 🛠️ Hướng dẫn từng bước thiết lập

### Bước 1: Tạo cặp SSH Key để GitHub kết nối tới VPS

Để GitHub Actions có thể SSH vào VPS của bạn một cách an toàn mà không cần dùng mật khẩu root:

1. Mở terminal trên máy tính của bạn (hoặc trên VPS) và chạy lệnh tạo SSH Key:
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy"
   ```
   *Khi được hỏi nơi lưu, nhấn Enter để chọn mặc định. Bỏ qua phần mật khẩu bảo vệ (nhấn Enter 2 lần).*

2. Thêm **Public Key** vào danh sách các key được phép đăng nhập trên VPS:
   ```bash
   cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

3. Copy nội dung **Private Key** (bắt đầu bằng `-----BEGIN OPENSSH PRIVATE KEY-----`):
   ```bash
   cat ~/.ssh/id_ed25519
   ```
   *Lưu trữ nội dung này lại để cấu hình GitHub Secrets ở bước tiếp theo.*

---

### Bước 2: Cấu hình GitHub Secrets cho Repository

Để bảo mật thông tin máy chủ của bạn, hãy thêm các biến bí mật vào GitHub Repository:

1. Truy cập vào Repository của bạn trên GitHub.
2. Chọn **Settings** -> **Secrets and variables** -> **Actions**.
3. Nhấp vào **New repository secret** và thêm lần lượt các biến sau:
   - `VPS_HOST`: Địa chỉ IP của VPS của bạn (ví dụ: `123.45.67.89`).
   - `VPS_USER`: Tên user dùng để đăng nhập SSH (thường là `ubuntu` hoặc `root`).
   - `VPS_SSH_KEY`: Dán toàn bộ nội dung **Private Key** đã copy ở Bước 1.
   - `VPS_PORT`: Cổng SSH (mặc định là `22`).

> [!WARNING]
> Tuyệt đối không bao giờ đưa trực tiếp IP, Username hoặc SSH Private Key vào các file mã nguồn đẩy lên GitHub. Hãy luôn sử dụng GitHub Secrets.

---

### Bước 3: Cấu hình File và Kích hoạt Workflow

Quy trình deploy đã được cấu hình sẵn để triển khai trực tiếp vào thư mục `/var/www/DATN` trên VPS của bạn:

1. File workflow cấu hình GitHub Actions nằm tại: [.github/workflows/deploy-registry.yml](file:///home/huutran/Documents/hoc%20tap/DATN/.github/workflows/deploy-registry.yml)
   - Đường dẫn thư mục đích trên VPS đã được thiết lập mặc định là `/var/www/DATN` (đồng bộ với thói quen sử dụng lệnh `cd /var/www/DATN` của bạn).
   
2. File cấu hình Docker Compose cho Production: [docker-compose.prod.yml](file:///home/huutran/Documents/hoc%20tap/DATN/docker-compose.prod.yml)
   - File này sử dụng biến `${GITHUB_REPOSITORY_LOWERCASE}` để kéo trực tiếp Docker image từ GitHub Package Registry về VPS mà không cần build local, giảm tải CPU/RAM cho VPS.

---

### Bước 4: Kiểm tra hoạt động của CI/CD

Sau khi cấu hình xong:
1. Commit các file cấu hình mới này và push lên GitHub branch `main` (hoặc branch chính của bạn):
   ```bash
   git add .github/ docker-compose.prod.yml docs/
   git commit -m "chore: setup production build-and-push CI/CD workflow"
   git push origin main
   ```
2. Truy cập tab **Actions** trên GitHub repository của bạn để xem quá trình build và deploy tự động hoạt động trực tiếp.
