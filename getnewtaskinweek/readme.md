GetNewTaskInWeek - Outlook Porter
Dự án giúp tự động hóa việc trích xuất danh sách công việc từ email người gửi cụ thể (ví dụ: BUI HUY HOANG) trong folder chuyên biệt ThamDinh của Outlook, sau đó tối ưu hóa và đẩy lên Google Sheets để quản lý tập trung.

🚀 Quy trình hoạt động (Workflow)
Ứng dụng được thiết kế theo mô hình 3 bước kiểm soát chặt chẽ:

Quét (Scan): Kết nối Outlook qua MAPI, tìm trong folder Inbox/ThamDinh, lọc theo tên người gửi và hiển thị Preview lên giao diện GUI.

Kiểm duyệt (Local Commit): Tối ưu hóa tiêu đề (xóa "Re:", "Fwd:"), loại bỏ dữ liệu trùng lặp và xuất ra file task_export.json.

Đồng bộ (Cloud Sync): Đẩy dữ liệu từ bản JSON đã kiểm duyệt lên Google Sheets thông qua Service Account API.

📂 Cấu trúc dự án
main.py: Chứa toàn bộ mã nguồn GUI (Tkinter), logic kết nối Outlook và Google Sheets API.

config.py: Nơi cấu hình các hằng số (Tên folder, Tên Sheet, Tên file credentials).

credentials.json: File xác thực của Google Cloud (phải nằm cùng thư mục với main.py).

task_export.json: File lưu trữ trung gian sau khi dữ liệu đã được làm sạch.

🛠 Cấu hình kỹ thuật quan trọng
1. Outlook Folder
Mặc định code tìm trong subfolder của Inbox:

inbox = outlook.GetDefaultFolder(6)

target_folder = inbox.Folders("ThamDinh")

2. Google Sheets API
Cần cấp quyền cho Service Account:

Email Service Account trong file JSON phải được Share vào Google Sheet với quyền Editor.

Phải kích hoạt đồng thời cả Google Sheets API và Google Drive API trên Google Cloud Console.


2.3. Email đã sử dụng: hieunavt4mail@gmail.com
đường link quản lý API:
Loại API: service Account

2.2. https://console.cloud.google.com/iam-admin/serviceaccounts?previousPage=%2Fapis%2Fcredentials%3Fproject%3Dgetnewtaskinweek&project=getnewtaskinweek
API json key: getnewtaskinweek-5a476d4f2124.json

2.1. Đường link google sheet: https://docs.google.com/spreadsheets/d/15MqT1bu6wMQ9_QjfmF6qlERHSr5_98mn72Xhj3BjQVM/edit?pli=1&gid=0#gid=0

3. Logic Tối ưu (Optimization)
Sử dụng Pandas để xử lý chuỗi:

drop_duplicates(): Xóa task trùng.

Regex r'^(Re:\s*|Fwd:\s*)': Làm sạch tiêu đề mail để báo cáo thẩm định trông chuyên nghiệp hơn.

📝 Nhật ký Debug (Lessons Learned)
Lỗi Response [200]: Đây là phản hồi thành công nhưng đôi khi gây Exception trong gspread. Đã xử lý bằng cách dùng cú pháp sheet.update(range_name='A1', values=...).

Lỗi 403 Drive API: Nhớ luôn bật Drive API cùng với Sheets API để tránh lỗi phân quyền file.

Đường dẫn file: Luôn sử dụng os.path.dirname(os.path.abspath(__file__)) để đảm bảo code tìm đúng file credentials.json ngay cả khi chạy app từ thư mục cha.

🔜 Hướng phát triển tương lai
Thêm bộ lọc theo khoảng thời gian (chỉ lấy mail trong 7 ngày gần nhất).

Thêm tính năng gửi thông báo qua Telegram/Zalo sau khi push Sheet thành công.

Hy vọng file README này sẽ là "bản đồ" hữu ích cho bạn. Chúc dự án tiếp theo của bạn suôn sẻ! Giờ mình bắt đầu dự án mới nào