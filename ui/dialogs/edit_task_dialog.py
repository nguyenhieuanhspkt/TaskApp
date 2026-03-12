from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate


class EditTaskDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chỉnh sửa hồ sơ")
        self.setFixedWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # --- INPUT ---
        self.group_in = QLineEdit(task_data.get('group_id', ''))
        self.title_in = QLineEdit(task_data.get('title', ''))
        
        # 1. Khởi tạo ComboBox Loại hồ sơ
        self.cb_category = QComboBox()
        # Ép dùng Style mặc định để không bị lỗi màu hover như bạn muốn
        from PyQt5.QtWidgets import QStyledItemDelegate
        self.cb_category.setItemDelegate(QStyledItemDelegate()) 
        
        self.cb_category.addItem("📁 Dự toán", "du_toan")
        self.cb_category.addItem("⚖️ Đấu thầu", "dau_thau")
        self.cb_category.addItem("🛠️ Khác", "tham_tra")

        # Tự động chọn đúng loại hiện tại
        current_cat = task_data.get('category', 'tham_tra')
        index = self.cb_category.findData(current_cat)
        if index >= 0:
            self.cb_category.setCurrentIndex(index)

        self.start_in = QDateEdit(calendarPopup=True)
        self.start_in.setDate(QDate.fromString(task_data.get('start_date', ''), "yyyy-MM-dd"))

        self.due_in = QDateEdit(calendarPopup=True)
        self.due_in.setDate(QDate.fromString(task_data.get('due_date', ''), "yyyy-MM-dd"))

        self.dl_in = QDateEdit(calendarPopup=True)
        self.dl_in.setDate(QDate.fromString(task_data.get('deadline', ''), "yyyy-MM-dd"))

        # --- FORM (QUAN TRỌNG: Phải addRow thì mới hiện ra giao diện) ---
        form.addRow("Mã nhóm:", self.group_in)
        form.addRow("Tên hồ sơ:", self.title_in)
        form.addRow("Loại hồ sơ:", self.cb_category) # 👈 BẠN THIẾU DÒNG NÀY
        form.addRow("Ngày nhận:", self.start_in)
        form.addRow("Ngày hẹn:", self.due_in)
        form.addRow("Deadline:", self.dl_in)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        # Lưu ý: Tên biến phải khớp với tên đã đặt ở trên (__init__)
        return {
            "title": self.title_in.text(),
            "group_id": self.group_in.text(),
            "category": self.cb_category.currentData(), 
            "start_date": self.start_in.date().toString("yyyy-MM-dd"),
            "due_date": self.due_in.date().toString("yyyy-MM-dd"),
            "deadline": self.dl_in.date().toString("yyyy-MM-dd")
        }
