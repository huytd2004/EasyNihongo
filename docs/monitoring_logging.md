# Hướng dẫn Thiết lập Monitoring & Logging cơ bản cho Docker + VPS

Tài liệu này hướng dẫn cách giám sát hoạt động máy chủ (Monitoring) và quản lý log (Logging) một cách gọn nhẹ, trực quan và không tốn nhiều tài nguyên của VPS.

---

## 1. Quản lý Log (Logging) với Dozzle & Docker Log Rotation

Mặc định khi chạy Docker lâu ngày, file log của các container sẽ phình to không giới hạn, rất dễ làm đầy ổ đĩa cứng của VPS.

### A. Docker Log Rotation (Đã cấu hình sẵn)
Trong file cấu hình [docker-compose.prod.yml](file:///home/huutran/Documents/hoc%20tap/DATN/docker-compose.prod.yml), tôi đã thêm cấu hình giới hạn kích thước log cho tất cả dịch vụ:
```yaml
x-logging: &default-logging
  logging:
    driver: "json-file"
    options:
      max-size: "10m" # Mỗi file log tối đa 10 Megabytes
      max-file: "3"   # Giữ lại tối đa 3 file log cũ nhất
```
> [!TIP]
> Việc này giúp bạn không bao giờ lo lắng việc logs làm đầy ổ đĩa VPS dẫn đến sập hệ thống (Disk Full).

### B. Dozzle - Real-time Log Viewer (Đã tích hợp sẵn)
Tôi đã thêm service **Dozzle** vào Docker Compose. Dozzle cung cấp một giao diện web siêu nhẹ (chỉ tốn khoảng 10MB RAM) để bạn theo dõi log thời gian thực của tất cả container (`backend`, `frontend`, `ai-pipeline`, `postgres`, `neo4j`).

*   **Cách truy cập**: Mở trình duyệt và truy cập `http://<IP-VPS-CỦA-BẠN>:8888`
*   **Chức năng**:
    *   Xem logs real-time của bất kỳ container nào chỉ với 1 click chuột.
    *   Tìm kiếm, lọc nội dung log theo keyword.
    *   Tải log file trực tiếp về máy tính.

---

## 2. Giám sát hệ thống (Monitoring) cơ bản trên VPS

Để theo dõi dung lượng CPU, RAM, Disk và Network của VPS thời gian thực, có hai công cụ cực kỳ gọn nhẹ và chuyên nghiệp mà bạn có thể áp dụng:

### Phương án A: Netdata (Khuyên dùng - Đã tích hợp sẵn qua Docker Compose)

**Netdata** là một hệ thống giám sát thời gian thực cực kỳ mạnh mẽ và đẹp mắt. Nó đã được tích hợp sẵn làm một service trong file cấu hình [docker-compose.prod.yml](file:///home/huutran/Documents/hoc%20tap/DATN/docker-compose.prod.yml). 

Khi bạn deploy dự án qua CI/CD, Netdata sẽ tự động được khởi chạy.

#### Sử dụng:
*   Mở trình duyệt truy cập: `http://<IP-VPS-CỦA-BẠN>:19999`
*   **Chức năng**:
    *   Giám sát trực quan dung lượng CPU, RAM, Disk, Network của máy chủ VPS thời gian thực.
    *   Tự động phát hiện các Docker container và vẽ biểu đồ hiệu năng (CPU, RAM, I/O) cho từng container riêng biệt (`backend`, `frontend`, `ai-pipeline`, `postgres`, `neo4j`).
    *   **Mẹo**: Netdata có sẵn cơ chế cấu hình cảnh báo (Alarm) qua Telegram/Email nếu RAM hoặc CPU bị quá tải.

---

### Phương án B: Portainer (Quản lý Container + Giám sát cơ bản)

Nếu bạn muốn có một giao diện Web vừa để giám sát vừa có thể **Start / Stop / Restart** các container một cách trực quan, **Portainer** là lựa chọn số một.

#### Cài đặt Portainer bằng Docker:
Chạy lệnh sau trên VPS:
```bash
docker volume create portainer_data
docker run -d -p 9000:9000 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/var/data portainer/portainer-ce:latest
```

#### Sử dụng:
*   Truy cập: `http://<IP-VPS-CỦA-BẠN>:9000`
*   Thiết lập mật khẩu Admin trong lần đăng nhập đầu tiên.
*   Chọn local environment để quản lý toàn bộ container của dự án `DATN`. Bạn có thể click vào icon graph của từng container để xem chi tiết biểu đồ CPU, RAM sử dụng.

---

## 3. Tổng kết kiến nghị cho Đồ án Tốt nghiệp
Khi thuyết trình đồ án tốt nghiệp, để gây ấn tượng mạnh với hội đồng chấm thi về phần vận hành (DevOps):
1. **Show Dozzle (`port 8888`)**: Trình diễn việc giám sát log lỗi từ API FastAPI hoặc Spring Boot trực tiếp khi client gửi request.
2. **Show Netdata (`port 19999`)**: Trình diễn biểu đồ VPS đang hoạt động ổn định, chứng minh Docker tối ưu hóa tài nguyên phần cứng tốt thế nào.
