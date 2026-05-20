#  API Health Monitor & Alert System

Một hệ thống Full-Stack toàn diện dùng để giám sát sức khỏe, thời gian phản hồi (uptime/response time) của các API Endpoints và tự động gửi cảnh báo qua Telegram khi hệ thống gặp sự cố.

Dự án này được xây dựng theo chuẩn Production-ready, áp dụng các kiến trúc và công nghệ hiện đại nhất dành cho môi trường doanh nghiệp.

---

## 🏗 Tổng quan Kiến trúc Hệ thống

Hệ thống được chia làm hai phần độc lập (Microservices Architecture), giao tiếp với nhau qua RESTful API, và được bảo mật bằng JWT Token.

### 1. Backend (Lõi xử lý & Scheduler)
*   **Ngôn ngữ & Framework:** Python 3.11, **FastAPI**.
*   **Cơ sở dữ liệu:** **SQLite** (sử dụng SQLAlchemy ORM). Cơ sở dữ liệu được cấu hình `check_same_thread=False` để tương thích với cơ chế xử lý đa luồng (multi-threading) của FastAPI.
*   **Background Job (Cơ chế chạy ngầm):** Sử dụng **APScheduler** (AsyncIOScheduler) được tích hợp thẳng vào vòng đời (Lifespan) của FastAPI.
*   **Xử lý mạng bất đồng bộ:** Thay vì kiểm tra từng API một cách tuần tự (rất chậm), hệ thống sử dụng **`httpx.AsyncClient`** kết hợp với **`asyncio.gather`** để gửi hàng loạt Request kiểm tra cùng một lúc. Điều này giúp hệ thống có thể mở rộng (scale) lên hàng ngàn endpoints mà không bị thắt nút cổ chai (bottleneck).
*   **Bảo mật:** Tích hợp xác thực **JWT (JSON Web Tokens)** sử dụng thuật toán mã hóa mật khẩu `bcrypt`. Chỉ những người dùng đã đăng nhập mới có thể truy cập và thao tác với API.

### 2. Frontend (Giao diện hiển thị)
*   **Công nghệ lõi:** **React 18** khởi tạo bằng **Vite** (nhanh hơn Webpack rất nhiều).
*   **Giao diện & UI/UX:** Sử dụng **Tailwind CSS** để thiết kế giao diện hiện đại, responsive. Các biểu tượng (Icons) sử dụng thư viện `lucide-react`.
*   **Trực quan hóa dữ liệu:** Sử dụng **Recharts** để vẽ biểu đồ động (Line Chart) theo thời gian thực, hiển thị độ trễ (latency) của 50 lần ping gần nhất.
*   **Kết nối Backend:** Sử dụng **Axios** kết hợp với cơ chế Interceptors để tự động đính kèm Token JWT vào mỗi Request, và tự động điều hướng người dùng về trang Đăng nhập nếu Token hết hạn.

### 3. Hệ thống Cảnh báo (Alerting)
*   Tích hợp trực tiếp với API của Telegram Bot.
*   Hệ thống có cơ chế nhận diện sự thay đổi trạng thái (State Change Detection). Nó so sánh kết quả của lần ping hiện tại với lần ping ngay trước đó. Chỉ khi trạng thái chuyển từ **Hoạt động (Up)** sang **Lỗi (Down)** thì nó mới gửi tin nhắn cảnh báo tới điện thoại người quản trị, tránh việc spam tin nhắn rác.

---

##  Cơ chế hoạt động (How it works)

1.  **Đăng nhập:** Người quản trị truy cập vào Web, đăng nhập bằng tài khoản mặc định (`admin` / `admin123`). React sẽ nhận lại một mã JWT Token từ FastAPI và lưu vào `localStorage`.
2.  **Thêm API cần giám sát:** Người dùng nhập URL của API cần theo dõi (Ví dụ: `https://api.github.com`) và mã HTTP mong đợi (Ví dụ: `200`).
3.  **Vòng lặp giám sát (Mỗi 1 phút):**
    *   Cứ mỗi 1 phút, công cụ Scheduler ẩn dưới Backend sẽ thức dậy.
    *   Nó lấy toàn bộ danh sách API trong CSDL.
    *   Bắn HTTP GET Request đồng loạt tới các API đó. Đo chính xác số mili-giây (ms) để nhận được phản hồi.
    *   Ghi kết quả (Thành công/Thất bại, Thời gian trễ) vào bảng `PingLog`.
    *   Nếu phát hiện một API vừa bị sập, lập tức gọi API của Telegram để gửi tin nhắn cảnh báo khẩn cấp.
4.  **Cập nhật giao diện (Mỗi 30 giây):**
    *   Trang Dashboard của React có một bộ đếm giờ (setInterval). Cứ 30 giây nó sẽ tự động gọi API lấy dữ liệu mới nhất từ Backend để vẽ lại biểu đồ và tính toán lại Tỷ lệ hoạt động ổn định (Uptime Percentage) mà người dùng không cần phải F5 tải lại trang.

---

##  Hướng dẫn Cài đặt & Chạy dự án

Dự án này hỗ trợ 2 cách chạy: Chạy thủ công từng phần hoặc Chạy bằng Docker (Khuyên dùng cho môi trường Production).

### Cách 1: Chạy hoàn toàn tự động bằng Docker (Khuyên dùng)
*Yêu cầu máy tính phải cài đặt sẵn Docker và Docker Compose.*

1. Mở Terminal tại thư mục gốc của dự án.
2. (Tùy chọn) Chỉnh sửa file `docker-compose.yml` để thêm Token Telegram của bạn nếu muốn test cảnh báo.
3. Chạy lệnh:
   ```bash
   docker-compose up --build
   ```
4. Đợi Docker tự động tải hệ điều hành ảo, cài đặt thư viện và khởi động.
5. Truy cập **http://localhost:3000** để sử dụng.

### Cách 2: Chạy thủ công trên máy tính (Dành cho Development)

#### Bước 2.1: Khởi động Backend (FastAPI)
Mở một Terminal mới:
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Dành cho Windows
# source venv/bin/activate # Dành cho Mac/Linux

pip install -r requirements.txt
uvicorn main:app --reload
```
*Backend sẽ chạy tại: `http://localhost:8000` (Có thể xem tài liệu API tại `/docs`)*

#### Bước 2.2: Khởi động Frontend (React)
Mở Terminal thứ hai:
```bash
cd frontend
npm install
npm run dev
```
*Frontend sẽ chạy tại: `http://localhost:3000`*

---

## � Thông tin Đăng nhập mặc định
*   **Username:** `admin`
*   **Password:** `admin123`