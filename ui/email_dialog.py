# ui/email_dialog.py
from ui.common_imports import *

class EmailDialog(QDialog):
    def __init__(self, emails, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duyệt Email")
        self.resize(500, 400)
        self.emails = emails
        self.selected_index = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for e in emails:
            self.list_widget.addItem(f"{e['subject']} — {e['from']} — {e['received']}")
        layout.addWidget(self.list_widget)

        btn = QPushButton("Tạo Task từ email đã chọn")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        
    def get_selected_email(self):
        idx = self.list_widget.currentRow()
        return idx if idx >= 0 else None


def show_email_dialog(self, messages):
    if not messages:
        QMessageBox.information(self, "Thông báo", "Không có email mới.")
        return

    # Chuyển danh sách message → dữ liệu gọn
    emails_data = []
    print (type(messages))
    for msg in messages:
        emails_data.append({
            "subject": msg.subject,
            "from": str(msg.sender.email_address) if msg.sender else "(Không rõ)",
            "received": msg.datetime_received.strftime("%Y-%m-%d %H:%M:%S")
        })

    dlg = EmailDialog(emails_data, self)
    if dlg.exec_():
        idx = dlg.get_selected_email()
        if idx is None:
            return

        email = emails_data[idx]
        task_data = {
            "title": f"📩 {email['subject']}",
            "start_date": email["received"].split(" ")[0],  # 👈 lấy ngày nhận email
            "due_date": datetime.now().strftime("%Y-%m-%d"),
            "deadline": datetime.now().strftime("%Y-%m-%d"),
            "author": "ADMIN",
            "status": "doing"
        }

        new_id = self.service.add_or_edit_task(task_data, edit_mode=False, edit_index=None)
        self.update_list()
        QMessageBox.information(self, "Thành công", f"Đã tạo công việc mới (ID {new_id}).")