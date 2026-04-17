import os, json, csv, getpass, subprocess, re,sys
from datetime import datetime

# Thư viện bên thứ ba
import xlsxwriter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QLineEdit, QDateEdit, QMessageBox, QLabel, QRadioButton, 
    QButtonGroup, QShortcut, QListWidgetItem, QMenu, QFileDialog, 
    QDialog, QComboBox
)
from PyQt5.QtCore import QDate, QTimer, Qt, QSize
from PyQt5.QtGui import QKeySequence, QIcon

# Module nội bộ (Local modules)
from utils import resource_path, is_folder_really_empty
from dialogs import (
    DashboardV2,
    EditTaskDialog,
    FinalReviewDialog,
    TaskHistoryDialog,
)

# Nạp module weeklyreport từ thư mục tạm của EXE
weekly_dir = resource_path("weeklyreport")
if weekly_dir not in sys.path:
    # Thêm thư mục chứa weeklyreport vào hệ thống
    sys.path.insert(0, os.path.dirname(weekly_dir))
from weeklyreport.main import WeeklyReportExporter

class TaskManager(QWidget):
    def __init__(self, root_folder):
        super().__init__()
# ICON
        app_icon = resource_path("logo.ico")
        if os.path.exists(app_icon):
            self.setWindowIcon(QIcon(app_icon))
        
        self.current_year = datetime.now().year
        self.root_folder = root_folder
        self.base_folder = os.path.join(self.root_folder, f"Năm {self.current_year}")
        self.file_path = os.path.join(self.base_folder, "TaskApp", "tasks.json")
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.current_user = getpass.getuser()

        is_admin = self.current_user.lower() in ["hieuna_3", "vt4"]
        role_text = "Quản trị viên (Admin)" if is_admin else "Người dùng (User)"

        self.setWindowTitle(f"Phần mềm Quản lý Hồ sơ Thẩm định - [{self.current_user}] - Quyền: {role_text}")
        self.resize(850, 650)
        self.tasks, self.filtered_tasks = [], []
        
        self.init_ui()
        self.load_tasks()
        self.setup_auto_refresh()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- HÀNG 1: THÔNG BÁO & ĐIỀU HÀNH ---
        top_row = QHBoxLayout()
        self.status_msg = QLabel("⚡ Hệ thống sẵn sàng")
        self.status_msg.setStyleSheet("color: #27AE60; font-weight: bold; font-size: 12px;")
        
        self.btn_dash = QPushButton("📊 DASHBOARD")
        self.btn_dash.clicked.connect(self.show_dashboard)
        self.btn_dash.setFixedSize(110, 28)
        self.btn_dash.setStyleSheet("background: #8E44AD; color: white; font-weight: bold; border-radius: 5px;")
        
        self.btn_report = QPushButton("📄 REPORT")
        self.btn_report.clicked.connect(self.export_report)
        self.btn_report.setFixedSize(100, 28)
        self.btn_report.setStyleSheet("background: #217346; color: white; font-weight: bold; border-radius: 5px;")
        
        # THÊM NÚT BÁO CÁO TUẦN VÀO ĐÂY
        self.btn_weekly = QPushButton("📅 WEEKLY")
        self.btn_weekly.clicked.connect(self.export_weekly_report_feature)
        self.btn_weekly.setFixedSize(100, 28)
        self.btn_weekly.setStyleSheet("background: #005A9E; color: white; font-weight: bold; border-radius: 5px;")
        
        # THÊM NÚT CÔNG CỤ AI VÀO ĐÂY
        self.btn_ai = QPushButton("🤖 AI")
        self.btn_ai.clicked.connect(self.show_ai_features)
        self.btn_ai.setFixedSize(100, 28)
        self.btn_ai.setStyleSheet("background: #FF6600; color: white; font-weight: bold; border-radius: 5px;")
        
        top_row.addWidget(self.status_msg)
        top_row.addStretch()
        top_row.addWidget(self.btn_dash)
        top_row.addWidget(self.btn_report)
        top_row.addWidget(self.btn_weekly)
        top_row.addWidget(self.btn_ai)
        layout.addLayout(top_row)

        # --- HÀNG 2: TÌM KIẾM ---
        search_row = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm nhanh hồ sơ...")
        self.search_input.setStyleSheet("height: 35px; border-radius: 6px; border: 1.5px solid #003399; padding-left: 10px;")
        self.search_input.textChanged.connect(self.update_list)

        # Thêm ComboBox chọn Tháng
        self.month_combo = QComboBox()
        self.month_combo.addItems(["Tất cả"] + [str(i) for i in range(1, 13)])
        self.month_combo.setFixedWidth(80)
        self.month_combo.currentIndexChanged.connect(self.update_list)
        
        # Thêm ComboBox chọn Năm
        self.year_combo = QComboBox()
        # Thêm "Tất cả" vào đầu danh sách, sau đó là dải năm tự động
        year_range = [str(i) for i in range(2025, self.current_year + 2)]
        self.year_combo.addItems(["Tất cả"] + year_range)
        
        # Mặc định vẫn để năm hiện tại để tránh danh sách quá dài khi vừa mở App
        self.year_combo.setCurrentText(str(self.current_year))
        self.year_combo.setFixedWidth(85)
        self.year_combo.currentIndexChanged.connect(self.update_list)

        search_row.addWidget(self.search_input, 8)
        search_row.addWidget(QLabel("Tháng:"))
        search_row.addWidget(self.month_combo)
        search_row.addWidget(QLabel("Năm:"))
        search_row.addWidget(self.year_combo)
        
        layout.addLayout(search_row)

        # --- HÀNG 3: NHẬP DỰ ÁN VÀ NGÀY THÁNG (Đã sửa lỗi Layout) ---
        input_row = QHBoxLayout()
        
        # Nhóm nhập tên và mã
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Tên dự án mới...")
        self.task_input.setStyleSheet("height: 30px; border-radius: 4px; border: 1px solid #ccc;")
        
        # --- THÊM COMBO PHÂN LOẠI Ở ĐÂY ---
        self.category_input = QComboBox()
        self.category_input.addItem("📁 Dự toán", "du_toan")
        self.category_input.addItem("⚖️ Đấu thầu", "dau_thau")
        self.category_input.addItem("🛠️ Thẩm tra và Khác", "tham_tra")
        self.category_input.setFixedWidth(130)
        # Sửa lỗi màu chữ trắng trùng nền khi Hover
        
        self.txt_group_id = QLineEdit()
        self.txt_group_id.setPlaceholderText("Mã nhóm (Ctrl+G)")
        self.txt_group_id.setFixedWidth(120)
        self.txt_group_id.setStyleSheet("height: 30px; border-radius: 4px; border: 1px solid #ccc; background: #F0F8FF;")
        
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.txt_group_id.setFocus)

        # Nhóm ngày tháng
        date_group = QHBoxLayout(); date_group.setSpacing(5)
        self.start_date = QDateEdit(calendarPopup=True); self.start_date.setDate(QDate.currentDate())
        self.due_date = QDateEdit(calendarPopup=True); self.due_date.setDate(QDate.currentDate())
        self.deadline_input = QDateEdit(calendarPopup=True); self.deadline_input.setDate(QDate.currentDate())
        
        for widget, label in [(self.start_date, "Nhận"), (self.due_date, "Hẹn"), (self.deadline_input, "DL")]:
            date_group.addWidget(QLabel(label))
            widget.setFixedWidth(95); widget.setStyleSheet("height: 25px;")
            date_group.addWidget(widget)

        # Đưa tất cả vào input_row theo đúng thứ tự
        input_row.addWidget(self.task_input, 4)
        input_row.addWidget(self.category_input) # Thêm ComboBox vào UI
        input_row.addWidget(self.txt_group_id, 2)
        input_row.addLayout(date_group, 4)
        layout.addLayout(input_row)

        # --- HÀNG 4: ACTION BUTTONS (Gộp nút Lưu và 3 nút trạng thái) ---
        action_row = QHBoxLayout()
        self.btn_save = QPushButton("➕ LƯU HỒ SƠ (Ctrl+S)")
        self.btn_save.clicked.connect(self.add_or_edit_task)
        self.btn_save.setStyleSheet("background: #0078D4; color: white; font-weight: bold; height: 32px; border-radius: 5px;")
        action_row.addWidget(self.btn_save, 2)

        # Danh sách trạng thái với phím tắt tương ứng
        status_configs = [
            ("doing", "Nhận lại (Alt+1)", "#555"),
            ("sent", "Ý kiến (Alt+2)", "#E67E22"),
            ("done", "Xong (Alt+3)", "#27AE60")
        ]

        for s, n, color in status_configs:
            btn = QPushButton(n)
            btn.setFixedWidth(110) # Tăng độ rộng để hiện đủ chữ phím tắt
            btn.setStyleSheet(f"background: white; border: 1px solid {color}; color: {color}; font-weight: bold; height: 30px; border-radius: 5px;")
            btn.clicked.connect(lambda _, x=s: self._update_status(x))
            action_row.addWidget(btn)
        layout.addLayout(action_row)
        # --- VÙNG CHÍNH: DANH SÁCH ---
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
    QListWidget {
        border-radius: 8px; 
        background: #FDFDFD; 
        border: 1px solid #DDD;
        outline: none; /* Bỏ viền xanh khi click */
    }
    QListWidget::item {
        border-bottom: 1px solid #EEE; /* TIỂU TIẾT 3: Đường kẻ ngăn cách giữa các hàng */
        padding: 2px;
    }
    QListWidget::item:hover {
        background-color: #EDEFF2; /* TIỂU TIẾT 1: Hiệu ứng Hover màu xanh nhạt rất nhẹ */
        border-radius: 5px;
    }
    QListWidget::item:selected {
        background-color: #E1E8F0;
        color: black;
    }
""")
        self.list_widget.itemDoubleClicked.connect(self.open_task_folder)
        
        # FIX CHUỘT PHẢI TẠI ĐÂY
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)
        
        f_layout = QHBoxLayout()
        self.filter_group = QButtonGroup()
        
        # Cấu hình: (Tên hiển thị, Phím tắt)
        filters = [
            ("Đang làm", "Ctrl+1"),
            ("Đã gửi", "Ctrl+2"),
            ("Hoàn thành", "Ctrl+3"),
            ("Tất cả", "Ctrl+4")
        ]

        for i, (text, shortcut) in enumerate(filters):
            # Hiển thị text kèm phím tắt để người dùng dễ nhớ
            rb = QRadioButton(f"{text} ({shortcut})")
            self.filter_group.addButton(rb, i) # Gán ID cho dễ quản lý
            
            if text == "Đang làm": 
                rb.setChecked(True)
            
            rb.toggled.connect(self.update_list)
            f_layout.addWidget(rb)
            
            # Đăng ký phím tắt cho từng Radio Button
            QShortcut(QKeySequence(shortcut), self).activated.connect(rb.animateClick)

        layout.addLayout(f_layout)

        self.setLayout(layout)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.add_or_edit_task)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: self.search_input.setFocus()
            )
        # 1. Khi đang ở ô tìm kiếm, nhấn mũi tên xuống sẽ nhảy vào danh sách
        self.search_input.installEventFilter(self) # Cần thêm dòng này để bắt sự kiện phím

        # 2. Phím tắt Enter để mở thư mục khi đang chọn item trong danh sách
        QShortcut(QKeySequence(Qt.Key_Return), self.list_widget).activated.connect(self.open_task_folder)
        QShortcut(QKeySequence(Qt.Key_Enter), self.list_widget).activated.connect(self.open_task_folder)
        
    # --- PHÍM TẮT CHUYỂN TRẠNG THÁI ---
        # Alt + 1: Nhận lại (doing)
        QShortcut(QKeySequence("Alt+1"), self).activated.connect(lambda: self._update_status("doing"))
        
        # Alt + 2: Ý kiến (sent)
        QShortcut(QKeySequence("Alt+2"), self).activated.connect(lambda: self._update_status("sent"))
        
        # Alt + 3: Xong (done)
        QShortcut(QKeySequence("Alt+3"), self).activated.connect(lambda: self._update_status("done"))
    def eventFilter(self, source, event):
        # Sử dụng QEvent.KeyPress thay vì số 10 để code rõ ràng hơn
        from PyQt5.QtCore import QEvent 
        
        if source is self.search_input and event.type() == QEvent.KeyPress:
            # Nếu nhấn phím Mũi tên xuống khi đang ở ô tìm kiếm
            if event.key() == Qt.Key_Down:
                if self.list_widget.count() > 0:
                    self.list_widget.setFocus()
                    self.list_widget.setCurrentRow(0)
                    return True
            
            # Nếu nhấn Enter khi đang ở ô tìm kiếm (Mở ngay kết quả đầu tiên)
            elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                if self.list_widget.count() > 0:
                    self.list_widget.setCurrentRow(0)
                    self.open_task_folder()
                    return True
                    
        return super().eventFilter(source, event)
    def sanitize_group_id(self, text):
        """Làm sạch Mã nhóm: Viết hoa, bỏ khoảng trắng đầu cuối và xóa ký tự cấm của Windows"""
        import re
        if not text: return ""
        # 1. Thay thế các ký tự \ / : * ? " < > | bằng dấu gạch ngang -
        clean_text = re.sub(r'[\\/*?:"<>|]', '-', text.strip())
        # 2. Trả về kết quả viết hoa để đồng bộ
        return clean_text.upper()
    
    # --- SỬA LỖI SHOW CONTEXT MENU (GỌI 1 LẦN DUY NHẤT) ---
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return

        row = self.list_widget.currentRow()
        task = self.filtered_tasks[row]
        task_author = task.get('author', '')

        # Kiểm tra quyền
        is_admin = self.current_user.lower() in ["hieuna_3", "vt4"]
        is_owner = task_author.lower() == self.current_user.lower()
        has_permission = is_admin or is_owner

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #CCC; } "
                           "QMenu::item { padding: 8px 25px; } "
                           "QMenu::item:selected { background: #003399; color: white; }")
        
        # --- NHÓM 1: CHỈNH SỬA & NHẬT KÝ ---
        edit_a = menu.addAction("✏️ Sửa tên hồ sơ")
        edit_a.setEnabled(has_permission)
        
        history_a = menu.addAction("📜 Xem nhật ký hoạt động") 
        menu.addSeparator() 
        
        # --- NHÓM 2: FILE VÀ XUẤT BẢN ---
        open_a = menu.addAction("📂 Mở thư mục vật lý")
        
        # Thêm lệnh xuất lại mẫu 01 TTD (Nếu đã rà soát)
        re_export_action = None
        if task.get('final_report'):
            re_export_action = menu.addAction("📑 Xuất Mẫu 01 TTD")

        # Thêm lệnh lưu PDF vào Kho (Chỉ khi hồ sơ đã Xong)
        save_vault_action = None
        if task.get('status') == 'done':
            save_vault_action = menu.addAction("📦 Lưu file PDF vào Kho lưu trữ")
        
        menu.addSeparator()

        # --- NHÓM 3: QUẢN TRỊ ---
        del_a = menu.addAction("🗑️ Xóa hồ sơ")
        del_a.setEnabled(has_permission)

        if not has_permission:
            menu.addSeparator()
            info_a = menu.addAction(f"🔒 Quyền thuộc về: {task_author}")
            info_a.setEnabled(False)

        # --- THỰC THI DUY NHẤT 1 LẦN ---
        action = menu.exec_(self.list_widget.viewport().mapToGlobal(pos))
        # --- FIX LỖI TẠI ĐÂY: Nếu không chọn menu nào thì thoát luôn ---
        if not action: 
            return
        # --- XỬ LÝ KẾT QUẢ ---
        if action == edit_a:
            self.edit_task_detail()
        elif action == history_a:
            self.show_task_history()
        elif action == open_a:
            self.open_task_folder()
        elif action == re_export_action: # Thêm xử lý cho nút xuất lại
            self.prompt_export_options(task)
        elif action == save_vault_action:
            self.handle_save_pdf_to_vault(task)
        elif action == del_a:
            self.delete_task()

    # --- HÀM LƯU PDF VÀO KHO LƯU TRỮ RIÊNG BIỆT ---
    def handle_save_pdf_to_vault(self, task):
        import os
        from PyQt5.QtWidgets import QInputDialog

        cat_key = task.get('category', 'tham_tra')
        g_id = task.get('group_id', '').strip()

        # 1. Rà soát Mã nhóm (Chỉ bắt buộc cho Đấu thầu/Thẩm tra)
        if cat_key in ['dau_thau', 'tham_tra'] and not g_id:
            text, ok = QInputDialog.getText(self, 'Mã nhóm', 'Nhập Mã nhóm để tạo folder:')
            if ok and text.strip():
                g_id = self.sanitize_group_id(text) # Dùng hàm làm sạch đã viết
                task['group_id'] = g_id
                self.save_tasks()
            else: return

        # 2. Xác định Năm từ báo cáo hoặc từ Task
        report = task.get('final_report', {})
        final_date = report.get('final_report_date', '')
        year_val = final_date.split('/')[-1] if '/' in final_date else str(task.get('year'))

        # 3. Bản đồ ánh xạ thư mục gốc
        cat_map = {'du_toan': "Dự toán", 'dau_thau': "Đấu thầu", 'tham_tra': "Thẩm tra và khác"}
        cat_name = cat_map.get(cat_key, "Thẩm tra và khác")
        
        # Đường dẫn cơ sở: .../Các BC Thẩm định/[Loại]/[Năm]
        # (Đảm bảo folder Năm luôn được tạo cho mọi loại hồ sơ)
        vault_path = os.path.join(self.root_folder, "Các BC Thẩm định", cat_name, year_val)

        # 4. PHÂN NHÁNH CHI TIẾT
        if cat_key in ['dau_thau', 'tham_tra']:
            # Tạo thêm subfolder: Năm-Mã nhóm (Ví dụ: 2026-XL01)
            package_folder = f"{year_val}-{g_id}"
            vault_path = os.path.join(vault_path, package_folder)
        
        # Đối với 'du_toan': vault_path dừng lại ở folder Năm.
        # Các file PDF dự toán sẽ nằm chung trong: .../Dự toán/2026/

        os.makedirs(vault_path, exist_ok=True)
        
        # 5. Gọi hàm chọn file và copy (Hàm này đã bỏ mã nhóm ở tên file như bạn yêu cầu)
        self.copy_pdf_to_destination(task, vault_path)  
    def copy_pdf_to_destination(self, task, vault_path):
        """
        Cho phép người dùng chọn file PDF, chọn loại BCTĐ và copy vào Kho.
        Tên file format: [Loại BCTĐ] - [Tên hồ sơ].pdf
        """
        import os, shutil, re
        from datetime import datetime
        from PyQt5.QtWidgets import QMessageBox, QFileDialog, QInputDialog

        # 1. Xác định thư mục làm việc của Task
        year_val = task.get('year') or task.get('start_date', '2026')[:4]
        task_path = os.path.join(self.root_folder, f"Năm {year_val}", task.get('folder'))

        if not os.path.exists(task_path):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thư mục làm việc!")
            return

        # 2. Bước 1: Chọn file PDF gốc
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file PDF báo cáo", task_path, "PDF Files (*.pdf)"
        )
        if not file_path: return

        # 3. Bước 2: Chọn loại tài liệu (BCTĐ)
        cat_key = task.get('category', '')
        doc_prefix = ""
        
        if cat_key in ['dau_thau', 'tham_tra']:
            options = ["BCTĐ KHLCNT", "BCTĐ HSMT", "BCTĐ KQĐGKT", "BCTĐ KQLCNT", "BCTĐ Khác"]
            item, ok = QInputDialog.getItem(
                self, "Loại báo cáo", "Đây là loại báo cáo thẩm định gì?", options, 0, False
            )
            if ok and item:
                doc_prefix = f"{item} - " # Ví dụ: "BCTĐ HSMT - "

        # 4. Chuẩn hóa tên file đích (BỎ MÃ NHÓM)
        # Công thức: [Loại BCTĐ] - [Tên hồ sơ].pdf
        clean_title = re.sub(r'[\\/*?:"<>|]', '-', task.get('title', 'Bao_cao'))
        
        new_filename = f"{doc_prefix}{clean_title}.pdf"
        dest_full_path = os.path.join(vault_path, new_filename)

        try:
            # 5. Thực hiện sao chép
            shutil.copy2(file_path, dest_full_path)
            
            # 6. Ghi nhật ký hoạt động
            now_str = datetime.now().strftime('%d/%m %H:%M')
            log_msg = f"{now_str}: Đã lưu PDF vào Kho ({new_filename})"
            
            if 'history' not in task: task['history'] = []
            task['history'].append(log_msg)
            self.save_tasks() 

            self.show_msg(f"Đã lưu thành công vào Kho!")
            
            # 7. Mở folder và chọn file
            import subprocess
            subprocess.Popen(f'explorer /select,"{dest_full_path}"')

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")
    def update_list(self):
        self.list_widget.clear()
        query = self.search_input.text().strip().lower()
        sel_month = self.month_combo.currentText()
        sel_year = self.year_combo.currentText()
        
        current_filter_text = self.filter_group.checkedButton().text()
        # Xử lý lấy target_status từ text của RadioButton (cắt bỏ phần phím tắt trong ngoặc)
        pure_filter_text = current_filter_text.split(" (")[0]
        target_status = {"Đang làm": "doing", "Đã gửi": "sent", "Hoàn thành": "done"}.get(pure_filter_text)
        
        pool = self.get_all_tasks_from_all_years()         
        self.filtered_tasks = []
        
        for t in pool:
            t_year = str(t.get('year', ''))
            t_status = t.get('status')
            t_group = str(t.get('group_id', '')).lower() # Lấy mã nhóm để lọc
            
            # --- LOGIC LỌC NĂM ---
            if sel_year == "Tất cả":
                match_year = True
            else:
                if t_year == sel_year:
                    match_year = True
                elif t_year < sel_year and t_status in ["doing", "sent"]:
                    match_year = True
                else:
                    match_year = False

            # --- CÁC ĐIỀU KIỆN LỌC KHÁC (Đã thêm lọc theo mã nhóm) ---
            # Người dùng có thể tìm theo Tên hồ sơ HOẶC Thư mục HOẶC Mã nhóm
            match_query = (query in t['title'].lower() or 
                           query in t.get('folder', '').lower() or 
                           query in t_group)
            
            match_status = (not target_status or t_status == target_status)
            
            t_date = t.get('start_date', '')
            t_month = t_date.split("-")[1] if "-" in t_date else ""
            match_month = (sel_month == "Tất cả" or t_month.lstrip('0') == sel_month)
            
            if match_query and match_status and match_month and match_year:
                self.filtered_tasks.append(t)

        self.filtered_tasks.sort(key=lambda x: (x.get("year", self.current_year), x.get("id", 0)), reverse=True)
        
        now = datetime.now()
        for t in self.filtered_tasks:
            cat_data = {
                "du_toan": ("DỰ TOÁN", "#3498DB"), # Màu xanh dương
                "dau_thau": ("ĐẦU THẦU", "#E67E22"), # Màu cam
                "tham_tra": ("KHÁC", "#95A5A6")      # Màu xám
            }
            cat_name, cat_color = cat_data.get(t.get('category'), ("N/A", "#333"))
            
            # Tạo tag HTML cho loại hồ sơ
            cat_html = (f"<span style='background-color: {cat_color}; color: white; "
                        f"border-radius: 3px; padding: 1px 4px; font-size: 9px; "
                        f"font-weight: bold; margin-right: 5px;'>{cat_name}</span>")
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 115)) # Tăng nhẹ chiều cao để vừa Mã nhóm
            
            # Badge Trạng thái
            status_data = {
                "doing": ("Đang làm", "#555", "#F0F0F0"),
                "sent":  ("Đã gửi", "#E67E22", "#FEF5ED"),
                "done":  ("Xong", "#27AE60", "#EBFAEF")
            }
            text_st, color_st, bg_st = status_data.get(t.get('status'), ("N/A", "#333", "#EEE"))
            badge_html = f"<span style='background-color: {bg_st}; color: {color_st}; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 10px;'>{text_st}</span>"
            
            # Mã nhóm (Group ID) - Hiển thị Tag màu xanh dương
            group_id = t.get('group_id', '').upper()
            group_html = ""
            if group_id:
                group_html = f"<span style='background-color: #E1F5FE; color: #0288D1; border: 1px solid #0288D1; border-radius: 3px; padding: 1px 5px; font-weight: bold; font-size: 10px; margin-right: 5px;'>⚓ {group_id}</span>"

            # Deadline màu sắc
            dl_style = "color: #888;"
            try:
                days = (datetime.strptime(t['deadline'], "%Y-%m-%d") - now).days
                if t.get('status') != 'done':
                    if days <= 0: dl_style = "color: white; background-color: #E74C3C; border-radius: 3px; padding: 0 3px;"
                    elif days <= 1: dl_style = "color: #E74C3C; font-weight: bold;"
            except: pass

            display = (
                f"<div style='margin: 2px; padding: 8px; font-family: \"Segoe UI\"; border-bottom: 1px solid #ECF0F1;'>"
                f"  <table width='100%' border='0' cellspacing='0' cellpadding='0'>"
                f"    <tr>"
                f"      <td style='font-size: 11px; color: #7F8C8D;'>"
                f"          <b>[{t.get('year')}]</b> - {t.get('folder')}"
                f"      </td>"
                f"      <td align='right'>{badge_html}</td>"
                f"    </tr>"
                f"  </table>"
                f"  <div style='margin-top: 5px;'>"
                f"    {cat_html}{group_html}" # Chèn nhãn loại hồ sơ vào đây
                f"    <span style='font-size: 14px; font-weight: bold; color: #2C3E50;'>{t['title']}</span>"
                f"  </div>"
                f"  <div style='margin-top: 6px;'>"
                f"    <small style='color: #95A5A6;'>📅 {t.get('start_date')} | 🎯 {t.get('due_date')} | </small>"
                f"    <small style='{dl_style}'>⏰ DL: {t.get('deadline')}</small>"
                f"  </div>"
                f"</div>"
            )
            
            label = QLabel(display)
            label.setTextFormat(Qt.RichText)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)

    def show_msg(self, txt):
        self.status_msg.setText(f"✓ {txt}"); QTimer.singleShot(3000, lambda: self.status_msg.setText("⚡ Sẵn sàng"))

    def get_max_physical_id(self):
        ids = [t.get('id', 0) for t in self.tasks]
        if os.path.exists(self.base_folder):
            for item in os.listdir(self.base_folder):
                match = re.search(r"Thẩm định (\d+)", item)
                if match: ids.append(int(match.group(1)))
        return max(ids + [0])

    def add_or_edit_task(self):
        title = self.task_input.text().strip()
        g_id = self.sanitize_group_id(self.txt_group_id.text()) 
        category = self.category_input.currentData()
        
        if not title: 
            return

        # --- RÀNG BUỘC MÃ NHÓM CHO ĐẤU THẦU & THẨM TRA KHÁC ---
        # Chỉ có 'du_toan' là được phép để trống Mã nhóm
        if category in ['dau_thau', 'tham_tra'] and not g_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Thiếu thông tin", 
                                f"Đối với loại hồ sơ '{self.category_input.currentText()}', "
                                "bắt buộc phải nhập Mã nhóm (Số hiệu gói thầu/văn bản)!")
            self.txt_group_id.setFocus() 
            return

        # --- LOGIC TẠO FOLDER VÀ LƯU DỮ LIỆU (Giữ nguyên như cũ) ---
        reused_folder = ""
        if os.path.exists(self.base_folder):
            for item in os.listdir(self.base_folder):
                if item.endswith("_da xoa") and is_folder_really_empty(os.path.join(self.base_folder, item)):
                    clean = item.replace("_da xoa", "")
                    try:
                        os.rename(os.path.join(self.base_folder, item), os.path.join(self.base_folder, clean))
                        reused_folder = clean; break
                    except: continue
        
        if reused_folder:
            f_name = reused_folder
            task_id = int(re.search(r"(\d+)", f_name).group(1))
        else:
            task_id = self.get_max_physical_id() + 1
            f_name = f"Thẩm định {task_id}_{self.current_user}"
            os.makedirs(os.path.join(self.base_folder, f_name), exist_ok=True)

        new_task = {
            "id": task_id, "year": self.current_year, "folder": f_name, 
            "title": title, "group_id": g_id, "category": category, 
            "status": "doing", "author": self.current_user,
            "start_date": self.start_date.date().toString("yyyy-MM-dd"), 
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "deadline": self.deadline_input.date().toString("yyyy-MM-dd"), 
            "history": [f"{datetime.now().strftime('%d/%m %H:%M')}: Tạo mới"]
        }

        self.tasks.append(new_task)
        self.save_tasks()
        
        self.task_input.clear()
        self.txt_group_id.clear() 
        self.category_input.setCurrentIndex(0)
        self.update_list()
        self.show_msg(f"Đã lưu hồ sơ {task_id}")

    def _update_status(self, stat):
        row = self.list_widget.currentRow()
        if row < 0: return
        task = self.filtered_tasks[row]
        
        # Kiểm tra quyền (Giữ nguyên logic của bạn)
        if not (self.current_user.lower() == "vt4" or task.get('author', '').lower() == self.current_user.lower()):
            QMessageBox.warning(self, "Từ chối", "Bạn không có quyền đổi trạng thái hồ sơ này!")
            return

        current_time = datetime.now().strftime('%d/%m %H:%M')
        if "history" not in task: task["history"] = []

        if stat == "done":
            # GỌI HÀM DÙNG CHUNG Ở ĐÂY
            self.execute_final_review(task)
        else:
            # Các trạng thái khác (doing, sent) xử lý như cũ
            msg = "[NGHIEP_VU] Gửi ý kiến Zalo" if stat == "sent" else f"[HE_THONG] Chuyển: {stat}"
            task["history"].append(f"{current_time}: {msg}")
            task['status'] = stat
            self.save_task_to_year(task) # Đảm bảo luôn dùng hàm lưu theo năm
            self.update_list()
        
        self.show_msg(f"Đã cập nhật mốc nghiệp vụ cho hồ sơ {task.get('id')}")

    def edit_task_detail(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        task = self.filtered_tasks[row] 
        
        # --- KIỂM TRA QUYỀN ---
        is_admin = self.current_user.lower() in ["hieuna_3", "vt4"]
        is_owner = task.get('author', '').lower() == self.current_user.lower()
        
        if not (is_admin or is_owner):
            QMessageBox.warning(self, "Từ chối", f"Hồ sơ này của {task.get('author')}. Bạn không có quyền sửa!")
            return
        
        dlg = EditTaskDialog(task, self)
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()
            # --- LÀM SẠCH MÃ NHÓM TẠI ĐÂY ---
            raw_g_id = new_data.get('group_id', '').strip()
            # Thay thế ký tự cấm Windows bằng dấu gạch ngang và viết hoa
            clean_g_id = re.sub(r'[\\/*?:"<>|]', '-', raw_g_id).upper()
            # CẬP NHẬT CÁC TRƯỜNG DỮ LIỆU
            task['title'] = new_data['title']
            task['group_id'] = clean_g_id # Gán bản đã làm sạch
            task['category'] = new_data.get('category', 'tham_tra') # <-- BỔ SUNG DÒNG NÀY
            task['start_date'] = new_data['start_date']
            task['due_date'] = new_data['due_date']
            task['deadline'] = new_data['deadline']
            
            if "history" not in task: task["history"] = []
            task['history'].append(f"{datetime.now().strftime('%d/%m %H:%M')}: [HE_THONG] Chỉnh sửa thông tin/phân loại hồ sơ")
            
            self.save_task_to_year(task) 
            self.update_list()
            self.show_msg("Đã cập nhật thông tin hồ sơ thành công!")

    def show_task_history(self):
            """
            Lấy thông tin hồ sơ đang chọn và hiển thị hộp thoại nhật ký
            """
            # 1. Xác định dòng người dùng đang chọn trên danh sách
            row = self.list_widget.currentRow()
            if row < 0:
                return
                
            # 2. Lấy dữ liệu của hồ sơ đó từ danh sách đã lọc (filtered_tasks)
            task_data = self.filtered_tasks[row]
            
            # 3. Khởi tạo hộp thoại xem nhật ký (đã import từ dialogs.py)
            # TaskHistoryDialog sẽ nhận vào toàn bộ object task_data
            try:
                from dialogs import TaskHistoryDialog # Đảm bảo import đúng
                dlg = TaskHistoryDialog(task_data, self)
                
                # 4. Hiển thị cửa sổ dưới dạng Modal
                dlg.exec_()
                
                # 5. Thông báo nhẹ cho người dùng
                self.show_msg(f"Đã xem nhật ký hồ sơ {task_data.get('id')}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể hiển thị nhật ký: {str(e)}")


    def open_task_folder(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        t = self.filtered_tasks[row]

        # Lấy năm từ task, nếu không có thì lấy 4 số đầu của start_date
        year_val = t.get('year') or t.get('start_date', '2026')[:4]

        p = os.path.join(self.root_folder, f"Năm {year_val}", t['folder'])
        if os.path.exists(p): 
            subprocess.Popen(f'explorer "{p}"')
        else:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thư mục:\n{p}")

    def delete_task(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        
        # 1. Lấy dữ liệu task từ danh sách đã lọc (chứa cả năm 2025/2026)
        task = self.filtered_tasks[row]
        task_id = task.get('id')
        task_year = task.get('year')
        task_folder = task.get('folder')

        # 2. Xác nhận xóa
        msg = f"Bạn có chắc chắn muốn xóa hồ sơ {task_id} của năm {task_year}?\n(Thư mục vật lý sẽ được đánh dấu '_da xoa')"
        if QMessageBox.question(self, "Xác nhận xóa", msg) == QMessageBox.Yes:
            
            # 3. Xử lý thư mục vật lý (Dò đúng năm)
            # Không dùng self.base_folder vì nó cố định năm hiện tại
            actual_year_path = os.path.join(self.root_folder, f"Năm {task_year}")
            old_dir_path = os.path.join(actual_year_path, task_folder)
            
            if os.path.exists(old_dir_path):
                try:
                    # Đổi tên thư mục để đánh dấu đã xóa (tránh mất dữ liệu thật)
                    os.rename(old_dir_path, old_dir_path + "_da xoa")
                except Exception as e:
                    QMessageBox.warning(self, "Lưu ý", f"Không thể đổi tên thư mục: {str(e)}")

            # 4. Xóa dữ liệu trong file JSON của đúng năm đó
            json_path = os.path.join(actual_year_path, "TaskApp", "tasks.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        year_tasks = json.load(f)
                    
                    # Lọc bỏ task có ID tương ứng
                    new_year_tasks = [t for t in year_tasks if str(t.get('id')) != str(task_id)]
                    
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(new_year_tasks, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật file dữ liệu: {str(e)}")

            # 5. Cập nhật lại bộ nhớ đệm self.tasks (nếu xóa đúng task của năm hiện tại)
            if str(task_year) == str(self.current_year):
                self.tasks = [t for t in self.tasks if str(t.get('id')) != str(task_id)]

            # 6. Làm mới giao diện
            self.update_list()
            if hasattr(self, 'current_dashboard') and self.current_dashboard.isVisible():
                fresh_tasks = self.get_all_tasks_from_all_years()
                self.current_dashboard.update_data_source(fresh_tasks)
            self.show_msg(f"Đã xóa hồ sơ {task_id} ({task_year})")

    def get_all_tasks_from_all_years(self):
        combined = []
        if not os.path.exists(self.root_folder): return []
        for n in os.listdir(self.root_folder):
            if n.startswith("Năm "):
                p = os.path.join(self.root_folder, n, "TaskApp", "tasks.json")
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f); y = n.replace("Năm ", "")
                        for x in data: x["year"] = y
                        combined.extend(data)
        return combined

    def load_tasks(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f: self.tasks = json.load(f)
            self.update_list()

    def save_tasks(self):
        with open(self.file_path, "w", encoding="utf-8") as f: json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    def save_task_to_year(self, task_data):
        target_year = task_data.get('year', self.current_year)
        # Ép kiểu year về string để tránh lỗi đường dẫn
        folder_name = f"Năm {target_year}"
        path = os.path.join(self.root_folder, folder_name, "TaskApp", "tasks.json")
        
        os.makedirs(os.path.dirname(path), exist_ok=True) # Đảm bảo thư mục tồn tại
        
        year_tasks = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                year_tasks = json.load(f)
        
        found = False
        for i, t in enumerate(year_tasks):
            if str(t['id']) == str(task_data['id']): # So sánh ID ép kiểu chuỗi cho chắc
                year_tasks[i] = task_data
                found = True
                break
        
        if not found:
            year_tasks.append(task_data)
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(year_tasks, f, indent=2, ensure_ascii=False)
        

    def setup_auto_refresh(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self.load_tasks); self.timer.start(200000)

    # Trong file main_window.py

    def show_dashboard(self):
        # Truyền TẤT CẢ dữ liệu để Dashboard tự lọc theo ý Sếp
        all_tasks = self.get_all_tasks_from_all_years() 
        
        from dialogs import DashboardV2
        # Khởi tạo và gán vào self để hàm handle có thể truy cập lại dashboard
        self.current_dashboard = DashboardV2(
            all_tasks, 
            self.month_combo.currentText(), 
            self.year_combo.currentText(),
            self.root_folder # <-- Truyền thêm biến này
            )
        
        # KẾT NỐI SIGNAL: Khi Dashboard yêu cầu rà soát hồ sơ
        self.current_dashboard.task_update_requested.connect(self.handle_dashboard_review)
        
        self.current_dashboard.exec_()
    def handle_dashboard_review(self, task):
        # --- BƯỚC 1: QUAN TRỌNG NHẤT - MỞ DIALOG RÀ SOÁT ---
        # Chúng ta dùng hàm 'execute_final_review' đã viết ở Main Window
        # Hàm này sẽ mở FinalReviewDialog -> Lưu file JSON -> Ghi History
        if self.execute_final_review(task):
            
            # --- BƯỚC 2: NẾU USER NHẤN "CHẤP NHẬN" TRÊN DIALOG ---
            if hasattr(self, 'current_dashboard') and self.current_dashboard.isVisible():
                
                # Quét lại ổ đĩa để lấy bản ghi vừa được lưu
                fresh_tasks = self.get_all_tasks_from_all_years()
                
                # Bơm dữ liệu mới vào Dashboard và ra lệnh vẽ lại
                # (Giả sử bạn đã viết hàm update_data_source trong DashboardV2)
                self.current_dashboard.update_data_source(fresh_tasks)
                
            self.show_msg(f"Đã cập nhật hồ sơ {task.get('id')} thành công!")
    # --- HÀM DÙNG CHUNG CHO CẢ MAIN VÀ DASHBOARD ---
    def execute_final_review(self, task):
        """Logic rà soát dữ liệu: Lưu file + Cập nhật bộ nhớ + Refresh UI"""
        from dialogs import FinalReviewDialog
        from datetime import datetime
        import os

        dlg = FinalReviewDialog(task, self)
        if dlg.exec_() == QDialog.Accepted:
            final_info = dlg.get_final_data()
            
            # 1. Cập nhật dữ liệu vào object task
            task['final_report'] = final_info 
            task['status'] = 'done'
            
            # 2. Ghi nhật ký chuẩn
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            if "history" not in task: task["history"] = []
            
            # Tránh ghi trùng nhật ký nếu rà soát nhiều lần
            log_msg = f"{current_time}: [NGHIEP_VU] Xong - Đã rà soát báo cáo"
            if not task["history"] or "[NGHIEP_VU] Xong" not in task["history"][-1]:
                task["history"].append(log_msg)

            # --- BƯỚC QUAN TRỌNG NHẤT: CẬP NHẬT BỘ NHỚ ĐỆM (self.tasks) ---
            # Nếu không có bước này, update_list() sẽ load lại dữ liệu cũ chưa có final_report
            found_in_memory = False
            for i, t in enumerate(self.tasks):
                if str(t.get('id')) == str(task.get('id')):
                    self.tasks[i] = task # Thay bằng object đã có final_report
                    found_in_memory = True
                    break
            
            # Nếu không tìm thấy trong self.tasks (trường hợp rà soát từ Dashboard năm cũ)
            # thì biến self.tasks không quan trọng bằng việc gọi update_list() ở dưới

            # 3. LƯU QUAN TRỌNG: Ghi xuống file JSON
            self.save_task_to_year(task)
            
            # 4. REFRESH GIAO DIỆN CHÍNH
            # Gọi trực tiếp để đồng bộ bảng danh sách ngay lập tức
            self.update_list()

            # 5. Thông báo nhẹ trên thanh trạng thái
            self.show_msg(f"Đã rà soát hồ sơ {task.get('id')}")

            # 6. Gọi hàm xuất file dùng chung
            self.prompt_export_options(task)
            return True
            
        return False
    def prompt_export_options(self, task):
        """Hộp thoại lựa chọn xuất file dùng chung"""
        from PyQt5.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Xuất hồ sơ rà soát")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"Hồ sơ: {task.get('title')}\n\nBạn muốn xuất Bảng thống kê tiến độ (Mẫu 01 TTD) định dạng nào?")
        
        btn_word = msg_box.addButton("Xuất Word", QMessageBox.ActionRole)
        btn_close = msg_box.addButton("Đóng", QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == btn_word:
            self.export_to_task_folder(task, "word")
    
    
    def export_to_task_folder(self, task, file_type):
        import os, re, subprocess
        from docxtpl import DocxTemplate # Import thư viện xử lý template
        from PyQt5.QtWidgets import QMessageBox
        from datetime import datetime
        # Hàm hỗ trợ tính khoảng cách ngày
        def days_between(d1, d2):
            try:
                # Chuyển từ định dạng dd/mm/yyyy sang object để trừ
                date1 = datetime.strptime(d1, "%d/%m/%Y")
                date2 = datetime.strptime(d2, "%d/%m/%Y")
                return abs((date2 - date1).days)
            except:
                return "..."
    
        # 1. Xác định đường dẫn
        year_val = task.get('year') or task.get('start_date', '2026')[:4]
        task_path = os.path.join(self.root_folder, f"Năm {year_val}", task.get('folder'))
        
        # Đường dẫn template của bạn
        template_path = os.path.join(self.root_folder, f"Năm {year_val}", "TaskApp", "Mẫu 01_TTD.docx")

        if not os.path.exists(template_path):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file mẫu Word trong TaskApp!")
            return

        # 2. Tạo tên file đích
        safe_title = re.sub(r'[\\/*?:"<>|]', '-', task.get('title', 'Bao_cao'))
        dest_file = os.path.join(task_path, f"Mau_01_TTD_{safe_title}.docx")

        try:
            # 3. ĐỔ DỮ LIỆU VÀO WORD
            doc = DocxTemplate(template_path)
            
            # Lấy dữ liệu rà soát
            report = task.get('final_report', {})
            
            # Chuẩn bị "túi quà" dữ liệu để gửi vào Word
            context = {
                'title': task.get('title'),
                'start_date': report.get('start_date'),
                'first_sent_date': report.get('first_sent_date'),
                'completion_date': report.get('completion_date'),
                'final_report_date': report.get('final_report_date'),
                # Tính toán số ngày tự động
                'diff_1_2': days_between(report.get('start_date'), report.get('first_sent_date')),
                'diff_3_4': days_between(report.get('completion_date'), report.get('final_report_date')),
            }

            # Tiến hành ghi đè dữ liệu vào các biến {{ }}
            doc.render(context)
            doc.save(dest_file) # Lưu file đã có dữ liệu

            # 4. THÔNG BÁO VÀ MỞ FILE
            self.show_msg("Đã xuất file Word thành công!")
            os.startfile(dest_file) # Mở thẳng file Word vừa tạo cho sếp xem

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể đổ dữ liệu vào Word: {str(e)}")
    def export_report(self):
        from datetime import datetime
        
        default_name = f"Bao_cao_Tham_Dinh_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu Báo Cáo Excel", default_name, "Excel Files (*.xlsx)")
        
        if not save_path: return

        try:
            pool = self.get_all_tasks_from_all_years()
            
            # Hàm hỗ trợ xử lý ngày tháng sang định dạng Excel hiểu được (float/datetime)
            def smart_to_excel_date(val):
                if val is None or val == "": return None
                s_val = str(val).strip()[:10] # Lấy YYYY-MM-DD
                try:
                    return datetime.strptime(s_val, "%Y-%m-%d")
                except:
                    return val

            # --- KHỞI TẠO WORKBOOK VÀ WORKSHEET (Dùng trực tiếp xlsxwriter) ---
            workbook  = xlsxwriter.Workbook(save_path)
            worksheet = workbook.add_worksheet('Báo cáo chi tiết')

            # --- ĐỊNH DẠNG (FORMAT) ---
            header_fmt = workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter', 
                'fg_color': '#2E75B6', 'font_color': 'white', 'border': 1
            })
            cell_fmt = workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'text_wrap': True
            })
            date_fmt = workbook.add_format({
                'num_format': 'dd/mm/yyyy', 'border': 1, 
                'align': 'center', 'valign': 'vcenter'
            })

            # --- GHI HEADER ---
            
            headers = ["Năm", "ID", "Mã nhóm", "Thư mục", "Tên hồ sơ", "Ngày nhận", "Ngày hẹn", "Deadline", "Chuyên viên", "Trạng thái", "Nhật ký"]
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header, header_fmt)

            # --- GHI DỮ LIỆU ---
            for row_idx, t in enumerate(pool, start=1):
                st_vn = {"doing": "Đang làm", "sent": "Đã gửi ý kiến", "done": "Hoàn thành"}.get(t.get('status'), t.get('status'))
                
                # Danh sách dữ liệu từng cột
                row_data = [
                    t.get('year'),
                    t.get('id'),
                    t.get('group_id', ''), 
                    t.get('folder'),
                    t.get('title'),
                    smart_to_excel_date(t.get('start_date')),
                    smart_to_excel_date(t.get('due_date')),
                    smart_to_excel_date(t.get('deadline')),
                    t.get('author'),
                    st_vn,
                    " | ".join(t.get('history', []))
                ]

                for col_idx, value in enumerate(row_data):
                    if col_idx in [4, 5, 6] and isinstance(value, datetime):
                        # Ghi định dạng ngày tháng cho cột 4, 5, 6
                        worksheet.write_datetime(row_idx, col_idx, value, date_fmt)
                    else:
                        worksheet.write(row_idx, col_idx, value, cell_fmt)

            # --- CHỈNH ĐỘ RỘNG CỘT ---
            worksheet.set_column('A:B', 8)   # Năm, ID
            worksheet.set_column('C:C', 20)  # Thư mục
            worksheet.set_column('D:D', 45)  # Tên hồ sơ
            worksheet.set_column('E:G', 14)  # Các ngày
            worksheet.set_column('H:I', 15)  # Chuyên viên, Trạng thái
            worksheet.set_column('J:J', 50)  # Nhật ký

            worksheet.freeze_panes(1, 0) # Cố định dòng đầu
            workbook.close() # Quan trọng: Phải đóng để lưu file

            self.show_msg("Xuất báo cáo Excel thành công!")
            os.startfile(save_path)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất file", f"Lỗi: {str(e)}")
            
    def export_weekly_report_feature(self):
        try:
            # Khởi tạo và truyền 'self.root_folder' (đường dẫn OneDrive user đã chọn)
            exporter = WeeklyReportExporter(self.root_folder,self.current_year)
            
            # Chạy lệnh xuất
            exporter.export()
            
            # (Tùy chọn) Thông báo thành công
            # self.show_status_message("Báo cáo tuần đã được mở!")
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Lỗi xuất báo cáo: {error_details}")
            # QMessageBox.critical(self, "Lỗi", f"Không thể xuất báo cáo: {str(e)}")
    def show_ai_features(self):
        if hasattr(self, 'ai_window') and self.ai_window.isVisible():
            self.ai_window.activateWindow()
            return
            
        try:
            # Gọi thẳng từ Package ai_hub
            from ai_hub.main_hub import AIWindow 
            self.ai_window = AIWindow()
            self.ai_window.show()
        except Exception as e:
            self.status_msg.setText(f"❌ Lỗi: {str(e)}")