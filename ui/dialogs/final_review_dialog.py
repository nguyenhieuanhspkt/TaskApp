from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QDateEdit, QLineEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIntValidator
from typing import Optional
from datetime import datetime

# =====================
# CONSTANTS
# =====================
DATE_FMT = "dd/MM/yyyy"
ISO_FMT = "yyyy-MM-dd"

# =====================
# HELPERS
# =====================
def to_qdate(date_str: Optional[str]) -> Optional[QDate]:
    """
    Parse string -> QDate an toàn cho cả ISO và VN format.
    """
    if not date_str or str(date_str).strip() == "" or date_str == "N/A":
        return None

    raw = str(date_str).strip()[:10]
    for fmt in (ISO_FMT, DATE_FMT):
        qd = QDate.fromString(raw, fmt)
        if qd.isValid():
            return qd
    return None

def parse_history(history: list):
    """Bóc tách lịch sử lấy mốc gửi đầu, cuối và số lần."""
    first_sent, last_sent, count = None, None, 0
    for h in history or []:
        if "[NGHIEP_VU] Gửi ý kiến" not in h:
            continue
        count += 1
        ts = h.split(":")[0].strip()
        if not first_sent: first_sent = ts
        last_sent = ts
    return first_sent, last_sent, count

# =====================
# DIALOG
# =====================
class FinalReviewDialog(QDialog):
    def __init__(self, task_data: dict, parent=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        
        # Lấy ngày gốc của Task để làm mốc fallback quan trọng nhất
        self.default_fallback_date = to_qdate(self.task_data.get("start_date")) or QDate.currentDate()

        self._setup_window()
        self._build_ui()
        self._load_data()
        self._validate_form()

    def _setup_window(self):
        self.setWindowTitle(f"Rà soát lập bảng thống kê tiến độ thẩm định - tên: {self.task_data.get('title', 'N/A')}")
        self.setFixedWidth(520)
        self.setStyleSheet("QDialog { background-color: white; }")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(14)

        self.date_start = self._date_edit()
        self.date_first = self._date_edit()
        self.txt_count = self._count_edit()
        self.date_last = self._date_edit()
        self.date_report = self._date_edit()

        form.addRow("1. Ngày đề nghị thẩm định:", self.date_start)
        form.addRow("2. Ngày gửi yêu cầu bổ sung làm rõ:", self.date_first)
        form.addRow("3. Số lần chỉnh sửa:", self.txt_count)
        form.addRow("4. Ngày đầy đủ nội dung yêu cầu làm rõ:", self.date_last)
        form.addRow("5. Ngày phát hành báo cáo thẩm định:", self.date_report)

        layout.addLayout(form)

        self.btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_btn = self.btn_box.button(QDialogButtonBox.Ok)
        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)
        layout.addWidget(self.btn_box)

        # Validate realtime khi thay đổi dữ liệu
        for w in (self.date_last, self.date_report, self.txt_count):
            if isinstance(w, QDateEdit):
                w.dateChanged.connect(self._validate_form)
            else:
                w.textChanged.connect(self._validate_form)

    def _date_edit(self) -> QDateEdit:
        w = QDateEdit(calendarPopup=True)
        w.setDisplayFormat(DATE_FMT)
        w.setMinimumDate(QDate(1900, 1, 1))
        # Không đặt SpecialValueText để tránh hiện "—" gây hiểu lầm, 
        # sẽ quản lý bằng logic mặc định bên dưới.
        return w

    def _count_edit(self) -> QLineEdit:
        w = QLineEdit()
        w.setAlignment(Qt.AlignCenter)
        w.setValidator(QIntValidator(0, 999))
        w.setStyleSheet("height: 30px; border-radius: 4px; border: 1px solid #ccc;")
        return w

    def _load_data(self):
        """Logic nạp dữ liệu thông minh với các cấp độ ưu tiên."""
        history = self.task_data.get("history", [])
        first_h, last_h, auto_count = parse_history(history)

        # 1. Ngày nhận hồ sơ (Cố định theo Task)
        self.date_start.setDate(self.default_fallback_date)
        # Khóa ô này nếu bạn không muốn user sửa ngày nhận ở đây
        # self.date_start.setEnabled(False) 

        # 2. Logic Mặc định (Fallback): 
        # Ưu tiên 1: Dữ liệu đã lưu trong báo cáo cũ (final_report_date, ...)
        # Ưu tiên 2: Dữ liệu bóc tách từ lịch sử (history)
        # Ưu tiên 3: Ngày nhận hồ sơ của Task (start_date)
        
        dates_to_load = [
            (self.date_first, self.task_data.get("first_sent_date") or first_h),
            (self.date_last,  self.task_data.get("completion_date") or last_h),
            (self.date_report, self.task_data.get("final_report_date"))
        ]

        for widget, val in dates_to_load:
            qd = to_qdate(val)
            if qd:
                widget.setDate(qd)
            else:
                # ⭐ Đây là điểm bạn yêu cầu: Lấy start_date của task nếu trống
                widget.setDate(self.default_fallback_date)

        # 3. Số lần chỉnh sửa
        saved_count = self.task_data.get("sent_count")
        self.txt_count.setText(str(saved_count if saved_count is not None else auto_count))

    def _validate_form(self):
        """Đảm bảo các ô không bị bỏ trống hoặc ngày không hợp lệ."""
        is_count_ok = bool(self.txt_count.text().strip())
        
        # Chỉ bật nút OK nếu có số lần chỉnh sửa
        # Bạn có thể thêm logic kiểm tra ngày cuối phải >= ngày đầu ở đây
        self.ok_btn.setEnabled(is_count_ok)

    def get_final_data(self):
        """Xuất dữ liệu đồng nhất định dạng VN."""
        return {
            "start_date": self.date_start.date().toString(DATE_FMT),
            "first_sent_date": self.date_first.date().toString(DATE_FMT),
            "sent_count": self.txt_count.text(),
            "completion_date": self.date_last.date().toString(DATE_FMT),
            "final_report_date": self.date_report.date().toString(DATE_FMT),
        }