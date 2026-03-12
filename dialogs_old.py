import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, 
    QFrame, QGraphicsDropShadowEffect, QListWidget, QWidget, QLineEdit, 
    QDateEdit, QFormLayout, QDialogButtonBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QDate
from PyQt5.QtGui import QPixmap, QColor, QFont

# Nhập các cấu hình từ dự án của bạn
from config import CONFIG_FILE, USER_PATHS
from utils import resource_path 

# =========================================================
# 1. WELCOME DIALOG (Giao diện gốc của bạn)
# =========================================================
class WelcomeUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 520)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        self.container.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 30px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(30, 35, 30, 35)
        c_layout.setSpacing(15)

        self.logo = QLabel()
        logo_file = resource_path("logo.png")
        if os.path.exists(logo_file):
            self.logo.setPixmap(QPixmap(logo_file).scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setText("EVN - TỔ THẨM ĐỊNH")
            self.logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #003399;")
        c_layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        title_lbl = QLabel("HỆ THỐNG QUẢN LÝ HỒ SƠ 2026")
        title_lbl.setStyleSheet("color: #2f3640; font-size: 14px; font-weight: bold;")
        c_layout.addWidget(title_lbl, alignment=Qt.AlignCenter)

        self.combo = QComboBox()
        self.combo.addItems(USER_PATHS.keys())
        self.combo.setStyleSheet("height: 45px; border-radius: 12px; border: 2px solid #edeff2; padding-left: 15px;")
        c_layout.addWidget(self.combo)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ff4757; font-size: 11px; font-weight: bold;")
        c_layout.addWidget(self.error_lbl, alignment=Qt.AlignCenter)

        self.btn_ok = QPushButton("BẮT ĐẦU LÀM VIỆC")
        self.btn_ok.setStyleSheet("background-color: #003399; color: white; height: 50px; border-radius: 15px; font-weight: bold;")
        self.btn_ok.clicked.connect(self.validate_and_start)
        c_layout.addWidget(self.btn_ok)

        layout.addWidget(self.container)

    def validate_and_start(self):
        path = USER_PATHS.get(self.combo.currentText())
        if path and os.path.exists(path):
            self.selected_path = path
            self.accept()
        else:
            self.error_lbl.setText("⚠ Không tìm thấy thư mục người dùng!")

# =========================================================
# 2. FINAL REVIEW DIALOG (Rà soát 5 mốc thời gian)
# =========================================================
class FinalReviewDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Rà soát kết quả thẩm định - ID: {task_data.get('id')}")
        self.setFixedWidth(500)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Bóc tách lịch sử để lấy các mốc tự động
        history = task_data.get('history', [])
        f_sent, l_sent, count = "", "", 0
        for h in history:
            if "[NGHIEP_VU] Gửi ý kiến" in h:
                count += 1
                dt = h.split(': ')[0]
                if not f_sent: f_sent = dt
                l_sent = dt

        self.txt_start = QLineEdit(task_data.get('start_date', ''))
        self.txt_first = QLineEdit(f_sent or "N/A")
        self.txt_count = QLineEdit(str(count))
        self.txt_last = QLineEdit(l_sent or "N/A")
        self.txt_report = QLineEdit(datetime.now().strftime('%d/%m/%Y'))

        form.addRow("1. Ngày nhận hồ sơ (Email):", self.txt_start)
        form.addRow("2. Ngày ý kiến Zalo lần 1:", self.txt_first)
        form.addRow("3. Số lần chỉnh sửa hồ sơ:", self.txt_count)
        form.addRow("4. Ngày đơn vị hoàn thiện hồ sơ:", self.txt_last)
        form.addRow("5. Ngày ký Báo cáo Thẩm định:", self.txt_report)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_final_data(self):
        return {
            "first_sent_date": self.txt_first.text(),
            "sent_count": self.txt_count.text(),
            "completion_date": self.txt_last.text(),
            "final_report_date": self.txt_report.text()
        }

# =========================================================
# 3. DASHBOARD V2 (Thống kê hiệu suất cho sếp)
# =========================================================
import os
import json
import logging
from datetime import datetime

# Đầy đủ Import từ PyQt5 - Không thiếu món nào
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, 
    QFrame, QGraphicsDropShadowEffect, QListWidget, QWidget, QLineEdit, 
    QDateEdit, QFormLayout, QDialogButtonBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QShortcut
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QDate
from PyQt5.QtGui import QPixmap, QColor, QFont, QKeySequence

# Import từ file dự án của bạn (Giữ nguyên cấu trúc cũ)
try:
    from config import CONFIG_FILE, USER_PATHS
    from utils import resource_path 
except ImportError:
    # Giá trị mặc định để code không bị crash khi chạy test độc lập
    CONFIG_FILE = "config.json"
    USER_PATHS = {"Admin": "C:/", "Guest": "D:/"}
    def resource_path(p): return p

# =========================================================
# 1. WELCOME DIALOG (GIỮ NGUYÊN GIAO DIỆN GỐC CỦA BẠN)
# =========================================================
class WelcomeUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 520)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        self.container.setStyleSheet("background-color: white; border: 1px solid #dcdde1; border-radius: 30px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(30, 35, 30, 35)
        c_layout.setSpacing(15)

        self.logo = QLabel()
        logo_file = resource_path("logo.png")
        if os.path.exists(logo_file):
            self.logo.setPixmap(QPixmap(logo_file).scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setText("EVN - TỔ THẨM ĐỊNH")
            self.logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #003399;")
        c_layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        title_lbl = QLabel("HỆ THỐNG QUẢN LÝ HỒ SƠ 2026")
        title_lbl.setStyleSheet("color: #2f3640; font-size: 14px; font-weight: bold;")
        c_layout.addWidget(title_lbl, alignment=Qt.AlignCenter)

        self.combo = QComboBox()
        self.combo.addItems(USER_PATHS.keys())
        self.combo.setStyleSheet("height: 45px; border-radius: 12px; border: 2px solid #edeff2; padding-left: 15px;")
        c_layout.addWidget(self.combo)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ff4757; font-size: 11px; font-weight: bold;")
        c_layout.addWidget(self.error_lbl, alignment=Qt.AlignCenter)

        self.btn_ok = QPushButton("BẮT ĐẦU LÀM VIỆC")
        self.btn_ok.setStyleSheet("background-color: #003399; color: white; height: 50px; border-radius: 15px; font-weight: bold;")
        self.btn_ok.clicked.connect(self.validate_and_start)
        # Thêm phím tắt Enter cho tiện
        self.btn_ok.setShortcut(QKeySequence(Qt.Key_Return))
        c_layout.addWidget(self.btn_ok)

        layout.addWidget(self.container)

    def validate_and_start(self):
        path = USER_PATHS.get(self.combo.currentText())
        if path and os.path.exists(path):
            self.selected_path = path
            self.accept()
        else:
            self.error_lbl.setText("⚠ Không tìm thấy thư mục người dùng!")

# =========================================================
# 2. DASHBOARD V2 (NÂNG CẤP LÕI XỬ LÝ - GIỮ GIAO DIỆN SANG TRỌNG)
# =========================================================
class DashboardV2(QDialog):
    def __init__(self, all_tasks, default_month, default_year):
        super().__init__()
        self.all_data = all_tasks 
        self.setWindowTitle("🚀 Phân Tích Hiệu Suất Thẩm Định")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("background-color: #F4F7F9;")

        main_layout = QVBoxLayout(self)

        # Bộ lọc (Sửa lỗi hiển thị nút chọn)
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("<b>Tháng:</b>"))
        self.cb_month = QComboBox()
        self.cb_month.addItems(["Tất cả"] + [str(i) for i in range(1, 13)])
        self.cb_month.setCurrentText(str(default_month))
        self.cb_month.setFixedWidth(100)
        filter_row.addWidget(self.cb_month)

        filter_row.addSpacing(20)

        filter_row.addWidget(QLabel("<b>Năm:</b>"))
        self.cb_year = QComboBox()
        self.cb_year.addItems(["Tất cả"] + [str(i) for i in range(2024, datetime.now().year + 2)])
        self.cb_year.setCurrentText(str(default_year))
        self.cb_year.setFixedWidth(100)
        filter_row.addWidget(self.cb_year)
        
        filter_row.addStretch()
        main_layout.addLayout(filter_row)

        # Các thẻ KPI (Dùng layout để cập nhật động)
        self.kpi_layout = QHBoxLayout()
        main_layout.addLayout(self.kpi_layout)

        # Bảng chi tiết
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Chuyên viên", "Xong", "Tồn", "⏱ Tổ làm", "⏳ Chờ ĐV", "🔄 Lần sửa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("QTableWidget { background: white; border-radius: 10px; }")
        main_layout.addWidget(self.table)

        # Kết nối sự kiện
        self.cb_month.currentIndexChanged.connect(self.refresh_stats)
        self.cb_year.currentIndexChanged.connect(self.refresh_stats)
        self.table.itemDoubleClicked.connect(self.view_pending_details)

        self.refresh_stats()

    def parse_dt(self, d_str):
        """Hàm xử lý ngày tháng linh hoạt cho 10 điểm chuyên nghiệp"""
        if not d_str or d_str == "N/A": return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try: return datetime.strptime(str(d_str)[:10], fmt)
            except: continue
        return None

    def create_box(self, label, value, color):
        box = QLabel(f"<div style='text-align:center;'>{label}<br><b style='font-size:16pt;'>{value}</b></div>")
        box.setStyleSheet(f"background: {color}; color: white; border-radius: 15px; padding: 15px; border: 1px solid rgba(0,0,0,0.1);")
        return box

    def refresh_stats(self):
        # Làm mới thẻ KPI
        for i in reversed(range(self.kpi_layout.count())): 
            self.kpi_layout.itemAt(i).widget().setParent(None)

        sel_m, sel_y = self.cb_month.currentText(), self.cb_year.currentText()
        user_map = {}
        t_int, t_ext, t_all, done_cnt = 0, 0, 0, 0
        self.current_filtered = []

        for t in self.all_data:
            dt_start = self.parse_dt(t.get('start_date'))
            if not dt_start: continue

            # Lọc dữ liệu
            match_y = (sel_y == "Tất cả" or str(dt_start.year) == sel_y)
            match_m = (sel_m == "Tất cả" or str(dt_start.month) == sel_m)
            
            if match_y and match_m:
                self.current_filtered.append(t)
                auth = t.get('author', 'N/A')
                if auth not in user_map:
                    user_map[auth] = {'done':0, 'pending':0, 'int_d':0, 'ext_d':0, 's_sum':0}
                
                if t.get('status') == 'done' and 'final_report' in t:
                    rep = t['final_report']
                    d_rep = self.parse_dt(rep.get('final_report_date'))
                    d_f = self.parse_dt(rep.get('first_sent_date'))
                    d_l = self.parse_dt(rep.get('completion_date'))

                    if d_rep and d_f and d_l:
                        total_days = max(0, (d_rep - dt_start).days)
                        ext_days = max(0, (d_l - d_f).days)
                        int_days = max(0, total_days - ext_days)

                        user_map[auth]['done'] += 1
                        user_map[auth]['int_d'] += int_days
                        user_map[auth]['ext_d'] += ext_days
                        user_map[auth]['s_sum'] += int(rep.get('sent_count', 0))
                        
                        t_int += int_days; t_ext += ext_days; t_all += total_days
                        done_cnt += 1
                else:
                    user_map[auth]['pending'] += 1

        # Cập nhật UI KPI
        avg_int = round(t_int/done_cnt, 1) if done_cnt > 0 else 0
        avg_ext = round(t_ext/done_cnt, 1) if done_cnt > 0 else 0
        avg_all = round(t_all/done_cnt, 1) if done_cnt > 0 else 0

        self.kpi_layout.addWidget(self.create_box("TỔ XỬ LÝ (AVG)", f"{avg_int} ngày", "#2E86C1"))
        self.kpi_layout.addWidget(self.create_box("CHỜ ĐƠN VỊ (AVG)", f"{avg_ext} ngày", "#E67E22"))
        self.kpi_layout.addWidget(self.create_box("TỔNG THỜI GIAN", f"{avg_all} ngày", "#27AE60"))

        # Cập nhật Bảng
        self.table.setRowCount(len(user_map))
        for row, (user, s) in enumerate(user_map.items()):
            d = s['done'] if s['done'] > 0 else 1
            self.table.setItem(row, 0, QTableWidgetItem(user))
            self.table.setItem(row, 1, QTableWidgetItem(str(s['done'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(s['pending'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{round(s['int_d']/d, 1)} n/hs"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{round(s['ext_d']/d, 1)} n/hs"))
            self.table.setItem(row, 5, QTableWidgetItem(f"~{round(s['s_sum']/d, 1)} lần"))

    def view_pending_details(self, item):
        user_name = self.table.item(item.row(), 0).text()
        details = [f"• {t['title']}" for t in self.current_filtered if t.get('author') == user_name and t.get('status') != 'done']
        QMessageBox.information(self, f"Hồ sơ tồn: {user_name}", "\n\n".join(details) if details else "Không có hồ sơ tồn.")

# Lưu ý: Các class EditTaskDialog và TaskHistoryDialog của bạn giữ nguyên vì đã quá chuẩn rồi.
# =========================================================
# 4. EDIT & HISTORY DIALOGS
# =========================================================
class EditTaskDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chỉnh sửa hồ sơ")
        self.setFixedWidth(450)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_in = QLineEdit(task_data.get('title', ''))
        self.group_in = QLineEdit(task_data.get('group_id', ''))
        self.start_in = QDateEdit(calendarPopup=True)
        self.start_in.setDate(QDate.fromString(task_data.get('start_date', ''), "yyyy-MM-dd"))
        self.dl_in = QDateEdit(calendarPopup=True)
        self.dl_in.setDate(QDate.fromString(task_data.get('deadline', ''), "yyyy-MM-dd"))
        
        form.addRow("Mã nhóm:", self.group_in)
        form.addRow("Tên hồ sơ:", self.title_in)
        form.addRow("Ngày nhận:", self.start_in)
        form.addRow("Deadline:", self.dl_in)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return {"title": self.title_in.text(), "group_id": self.group_in.text().upper(),
                "start_date": self.start_in.date().toString("yyyy-MM-dd"),
                "deadline": self.dl_in.date().toString("yyyy-MM-dd")}

class TaskHistoryDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nhật ký hoạt động")
        self.setFixedSize(450, 400)
        layout = QVBoxLayout(self)
        list_w = QListWidget()
        for h in reversed(task_data.get('history', [])): list_w.addItem(h)
        layout.addWidget(list_w)
        btn = QPushButton("Đóng"); btn.clicked.connect(self.accept); layout.addWidget(btn)