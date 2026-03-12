from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSignal # Thêm pyqtSignal
import os, subprocess # Đảm bảo đã import các thư viện này
class DashboardV2(QDialog):
    # Khai báo tín hiệu: Gửi đi một Dictionary (dữ liệu của task)
    task_update_requested = pyqtSignal(dict)
    def __init__(self, all_tasks, default_month, default_year,root_folder):
        super().__init__()
        self.all_data = all_tasks 
        self.root_folder = root_folder
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
    def open_task_folder_logic(self, t):
        """Logic mở folder y hệt Main Window của bạn"""
        # Lấy năm từ task, nếu không có thì lấy 4 số đầu của start_date
        year_val = t.get('year') or t.get('start_date', '2026')[:4]
        
        folder_name = t.get('folder')
        if not folder_name:
            QMessageBox.warning(self, "Lỗi", "Hồ sơ này chưa khai báo thư mục.")
            return

        p = os.path.join(self.root_folder, f"Năm {year_val}", folder_name)
        
        if os.path.exists(p): 
            # Dùng Popen giống hệt Main để mở Explorer
            subprocess.Popen(f'explorer "{p}"')
        else:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thư mục:\n{p}")
    def show_pending_context_menu(self, pos, list_widget, parent_dialog):
        item = list_widget.itemAt(pos)
        if not item: return
        
        task_data = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #CCC; } QMenu::item { padding: 8px 25px; }")
        
        act_open = menu.addAction("📂 Mở thư mục hồ sơ")
        act_review = menu.addAction("✏️ Rà soát kết quả")
        
        action = menu.exec_(list_widget.viewport().mapToGlobal(pos))
        
        if action == act_open:
            self.open_task_folder_logic(task_data) # Gọi hàm logic y hệt Main
        elif action == act_review:
            self.trigger_update(item, parent_dialog)
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
    def update_data_source(self, fresh_tasks):
        """Hàm này dùng để MainWindow bơm dữ liệu mới nhất vào"""
        self.all_data = fresh_tasks
        # Sau khi có dữ liệu mới, gọi hàm refresh_stats để tính toán lại toàn bộ
        self.refresh_stats()

    def refresh_stats(self):
        self.table.setRowCount(0)
        for i in reversed(range(self.kpi_layout.count())): 
            w = self.kpi_layout.itemAt(i).widget()
            if w: w.deleteLater()
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
        user_name = self.table.item(item.row(), 0).text().strip()
        pending_tasks = []

        for t in self.current_filtered:
            if str(t.get('author', 'N/A')).strip() != user_name:
                continue
            
            # --- PHÂN TÍCH LÝ DO TỒN (Logic đồng bộ với refresh_stats) ---
            status_raw = t.get('status', 'N/A')
            reason = ""
            is_done = False

            if status_raw != 'done':
                reason = f"Chưa hoàn thành ({status_raw})"
            elif 'final_report' not in t:
                reason = "Thiếu dữ liệu final_report"
            else:
                rep = t['final_report']
                d_rep = self.parse_dt(rep.get('final_report_date'))
                d_f = self.parse_dt(rep.get('first_sent_date'))
                d_l = self.parse_dt(rep.get('completion_date'))
                
                if not (d_rep and d_f and d_l):
                    missing = []
                    if not d_rep: missing.append("Ngày BC")
                    if not d_f: missing.append("Ngày gửi đầu")
                    if not d_l: missing.append("Ngày HT")
                    reason = f"Thiếu mốc ngày: {', '.join(missing)}"
                else:
                    is_done = True # Hồ sơ chuẩn, không tính là tồn

            if not is_done:
                t_copy = t.copy()
                t_copy['pending_reason'] = reason # Đóng dấu lý do vào task
                pending_tasks.append(t_copy)

        if not pending_tasks:
            QMessageBox.information(self, "Thông báo", f"Chuyên viên {user_name} không có hồ sơ tồn.")
            return

        # --- HIỂN THỊ DANH SÁCH CHI TIẾT ---
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle(f"Chi tiết tồn: {user_name}")
        detail_dialog.setMinimumSize(650, 450)
        layout = QVBoxLayout(detail_dialog)

        list_widget = QListWidget()
        
        list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid #EEE; padding: 10px; }")
        # KÍCH HOẠT CHUỘT PHẢI
        list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        list_widget.customContextMenuRequested.connect(
            lambda pos: self.show_pending_context_menu(pos, list_widget, detail_dialog)
        )
        
        for t in pending_tasks:
            reason = t['pending_reason']
            # Định dạng màu sắc cho lý do
            color = "red" if "Thiếu" in reason else "#2E86C1"
            
            # Tạo Widget hiển thị chuyên nghiệp
            display_text = f"📌 <b>{t.get('title', 'N/A')}</b><br>" \
                           f"📅 Bắt đầu: {t.get('start_date', 'N/A')} | ⚠️ Lý do: <span style='color: {color};'>{reason}</span>"
            
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, t) # Lưu task data để trigger_update dùng
            
            # Dùng QLabel để render HTML (cho phép in đậm, đổi màu)
            label = QLabel(display_text)
            label.setWordWrap(True)
            label.setContentsMargins(10, 5, 10, 5)
            
            list_item.setSizeHint(label.sizeHint())
            list_widget.addItem(list_item)
            list_widget.setItemWidget(list_item, label)

        # Kết nối sự kiện Double Click
        list_widget.itemDoubleClicked.connect(lambda it: self.trigger_update(it, detail_dialog))

        layout.addWidget(QLabel(f"<b>Tổng cộng {len(pending_tasks)} hồ sơ tồn. Double-click để xử lý:</b>"))
        layout.addWidget(list_widget)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(detail_dialog.accept)
        layout.addWidget(btn_close)

        detail_dialog.exec_()
        
        
        
    def trigger_update(self, item, parent_popup):
        task_data = item.data(Qt.UserRole)
        reason = task_data.get('pending_reason', '')
        
        # Nếu lý do là đang làm (status != done), có thể nhắc nhở user
        if "Chưa hoàn thành" in reason:
            msg = QMessageBox.warning(self, "Cảnh báo", 
                                     "Hồ sơ này chưa hoàn tất nghiệp vụ. Bạn vẫn muốn cập nhật báo cáo sớm?",
                                     QMessageBox.Yes | QMessageBox.No)
            if msg == QMessageBox.No: return

        self.task_update_requested.emit(task_data)
        parent_popup.accept()
        
    def open_task_folder(self, task):
        """Tận dụng logic mở folder từ MainWindow"""
        import os
        # LƯU Ý: Bạn cần đảm bảo MainWindow đã truyền root_folder vào Dashboard
        # Nếu chưa, bạn có thể tạm thời fix cứng hoặc lấy từ parent.
        root = "D:/HoSoThamDinh" # Đường dẫn gốc của bạn
        
        year = task.get('year') or task.get('start_date', '2026')[:4]
        folder_name = task.get('folder')
        
        if not folder_name:
            QMessageBox.warning(self, "Lỗi", "Hồ sơ này không có thông tin thư mục.")
            return

        path = os.path.join(root, f"Năm {year}", folder_name)
        
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.critical(self, "Lỗi", f"Đường dẫn không tồn tại:\n{path}")