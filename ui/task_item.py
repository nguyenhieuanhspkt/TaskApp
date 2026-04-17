from PyQt5.QtWidgets import QWidget, QListWidgetItem, QLabel
from PyQt5.QtCore import Qt
from datetime import datetime

from datetime import datetime, timedelta
from PyQt5.QtWidgets import QListWidgetItem, QLabel
from PyQt5.QtCore import Qt

class TaskItemWidget(QWidget):
    def __init__(self):
        super().__init__()

   

    def create_task_item(self, task):
        # 1. Hàm nội bộ để xử lý ngày tháng linh hoạt (Clean dữ liệu)
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Thử định dạng chuẩn YYYY-MM-DD
                return datetime.strptime(str(date_str).split(' ')[0], "%Y-%m-%d")
            except ValueError:
                try:
                    # Thử định dạng số của Excel (Serial Date)
                    excel_date_num = int(float(date_str))
                    return datetime(1899, 12, 30) + timedelta(days=excel_date_num)
                except (ValueError, TypeError):
                    return None

        # 2. Lấy dữ liệu ngày tháng đã chuẩn hóa
        start_date_obj = parse_date(task.get("start_date", ""))
        due_date_obj = parse_date(task.get("due_date", ""))
        
        # Chuẩn hóa hiển thị (để đưa vào HTML)
        start_date_display = start_date_obj.strftime("%d/%m/%Y") if start_date_obj else task.get("start_date", "N/A")
        due_date_display = due_date_obj.strftime("%d/%m/%Y") if due_date_obj else task.get("due_date", "N/A")

        # 3. Tính "tuổi" của task
        task_age_str = ""
        if start_date_obj:
            days_old = (datetime.now() - start_date_obj).days
            # Chỉ hiển thị nếu task chưa xong hoặc tùy mục đích của bạn
            task_age_str = f" | 🕓 {days_old} ngày"

        # 4. Thiết lập Icon và Nội dung HTML
        icon = {"done": "✅", "sent": "📨", "doing": "⏳"}.get(task.get("status"), "❓")
        
        html = (
            f"{icon} <b>[{task.get('folder','')}]</b> {task.get('title','')}<br>"
            f"📅 {start_date_display} → 🎯 {due_date_display} | "
            f"⏰ {task.get('deadline','')} — 👤 {task.get('author','')}{task_age_str}"
        )

        # 5. Tạo Widget hiển thị trong QListWidget
        item = QListWidgetItem()
        label = QLabel()
        label.setText(html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        
        # Thêm một chút padding cho dễ nhìn
        label.setStyleSheet("padding: 5px;")
        
        # Cập nhật kích thước cho item
        label.adjustSize()
        item.setSizeHint(label.sizeHint())
        
        return item, label
