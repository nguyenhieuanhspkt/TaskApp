from ui.common_imports import *
from ui.task_item import TaskItemWidget
from ui.email_dialog import show_email_dialog
from services.task_service import TaskService
from services.email_service import EmailLoaderThread

from ui.widgets.toast_message import show_message
class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.service = TaskService()
        self.edit_mode = False
        self.edit_index = None
        self.init_ui()
        self.current_user = getpass.getuser()
        # Lấy dữ liệu từ service
        self.tasks = self.service.load_tasks()  
        for k in self.tasks.keys():
            print(k, type(k))
        self.update_list()
        self.setup_auto_refresh()
        self.tasks = {}
        self.refresh_tasks()


    # ---------------- AUTO REFRESH ----------------
    def setup_auto_refresh(self):
        if self.edit_mode == False:
            self.show_message("Tự động làm mới sau 30s", color="#2196F3", duration=2000)
            return
        else:
            self.update_list()
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.refresh_tasks)
            self.timer.start(30 * 1000)
    def refresh_tasks(self):
        self.tasks = self.service.load_tasks()
        self.update_list()
    # ---------------- UI ----------------
    def init_ui(self):
        layout = QVBoxLayout()
        # --- Thanh tìm kiếm ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_input.textChanged.connect(self.update_list)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        shortcut_focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_focus_search.activated.connect(self.search_input.setFocus)
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self.on_escape_pressed)



        # --- Nhập công việc ---
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Nhập hoặc sửa công việc...")
        input_layout.addWidget(self.task_input)
        layout.addLayout(input_layout)

        # --- Ngày ---
        date_layout = QHBoxLayout()
        # Tạo date_edit start_date trước
        date_layout.addWidget(QLabel("📅 Ngày nhận:"))
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date)

        # Tạo due_date với mặc định là start_date + 3
        date_layout.addWidget(QLabel("🎯 Ngày hẹn HT:"))
        self.due_date = QDateEdit(calendarPopup=True)
        self.due_date.setDate(self.start_date.date().addDays(3))
        date_layout.addWidget(self.due_date)

        # Tạo deadline_input với mặc định là start_date + 3
        date_layout.addWidget(QLabel("⏰ Deadline:"))
        self.deadline_input = QDateEdit(calendarPopup=True)
        self.deadline_input.setDate(self.start_date.date().addDays(3))
        date_layout.addWidget(self.deadline_input)

        layout.addLayout(date_layout)

        # --- Nút ---
        btn_layout = QHBoxLayout()
        buttons = [
            ("➕ Thêm / Lưu", self.handleAddEdit, None),
            ("✏️ Sửa", self.edit_task, None),
            ("⏳ Đang làm", self.mark_doing, "#2196F3"),
            ("📨 Đã gửi", self.mark_sent, "#FF9800"),
            ("✅ Hoàn thành", self.mark_done, "#4CAF50"),
            ("🗑️ Xóa", self.delete_task, None),
            ("🔄 Làm mới", self.update_list, None),
            ("📧 Duyệt Email", self.handleBrowseEmail, None),
        ]
        for text, func, color in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            if color:
                btn.setStyleSheet(f"background-color:{color};color:white;font-weight:bold;")
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # --- List ---
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.list_widget)
    

        # --- Bộ lọc ---
        filter_layout = QHBoxLayout()
        self.filter_all = QRadioButton("Tất cả")
        self.filter_pending = QRadioButton("Đang làm ⏳")
        self.filter_sent = QRadioButton("Đã gửi 📨")
        self.filter_done = QRadioButton("Đã hoàn thành ✅")
        self.filter_all.setChecked(True)
        for rb in [self.filter_all, self.filter_pending, self.filter_sent, self.filter_done]:
            filter_layout.addWidget(rb)
            rb.toggled.connect(self.update_list)
        layout.addLayout(filter_layout)
        self.filter_group = QButtonGroup()
        for rb in [self.filter_all, self.filter_pending, self.filter_sent, self.filter_done]:
            self.filter_group.addButton(rb)

        # --- Toast ---
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("background-color:rgba(50,50,50,180);color:white;padding:8px 16px;border-radius:8px;font-weight:600;")
        self.info_label.setVisible(False)
        layout.addWidget(self.info_label)

        self.setLayout(layout)
        # self.update_list()
    def filter(self):
        # Lấy danh sách task dưới dạng list
        tasks_list = list(self.tasks.values())  # chuyển dict sang list
            # Áp filter theo trạng thái
        if self.filter_done.isChecked():
            filtered_tasks = [t for t in tasks_list if t["status"] == "done"]
        elif self.filter_sent.isChecked():
            filtered_tasks = [t for t in tasks_list if t["status"] == "sent"]
        elif self.filter_pending.isChecked():
            filtered_tasks = [t for t in tasks_list if t["status"] == "doing"]
        else:
            filtered_tasks = tasks_list.copy()  # đã là list

        query = self.search_input.text().strip().lower()
        if query:
            filtered_tasks = [t for t in filtered_tasks if query in t["title"].lower()]
        return filtered_tasks 
    # ---------------- Hiển thị ----------------
    def update_list(self):
        self.filtered_tasks = self.filter()
        self.filtered_tasks.sort(key=lambda x: x.get("start_date", "9999-12-31"))

        self.list_widget.clear()

        task_factory = TaskItemWidget()

        for task in self.filtered_tasks:
            item, label = task_factory.create_task_item(task)
            item.setData(Qt.UserRole, task["id"])   # 🔥 gắn id
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)

        self.show_message(
            f"Đang tải... {len(self.filtered_tasks)} công việc",
            color="#2196F3",
            duration=1000
        )

        
        # for t in self.filtered_tasks:
        #     icon = {"done": "✅", "sent": "📨", "doing": "⏳"}.get(t.get("status"), "❓")
        #     html = f"{icon} <b>[{t.get('folder','')}]</b> {t.get('title','')}<br>📅 {t.get('start_date','')} → 🎯 {t.get('due_date','')} | ⏰ {t.get('deadline','')} — {t.get('author','')}"
            
        #     item = QListWidgetItem()
        #     label = QLabel()
        #     label.setText(html)
        #     label.setWordWrap(True)
        #     label.setTextFormat(Qt.RichText)
        #     # tự động chiều cao theo nội dung
        #     label.adjustSize()
        #     item.setSizeHint(label.sizeHint())
        #     self.list_widget.addItem(item)
        #     self.list_widget.setItemWidget(item, label)
    
# ---------------- Xử lý sự kiện ----------------
#  LƯU CÔNG VIỆC MỚI HOẶC SỬA CÔNG VIỆC
    def handleAddEdit(self):
        if not self.task_input.text().strip():
            self.show_message("Vui lòng nhập tên công việc", color="#f44336")
            return

        task_data = {
            "title": self.task_input.text(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "deadline": self.deadline_input.date().toString("yyyy-MM-dd"),
            "author": self.current_user
        }

        if self.edit_mode:
            self.service.edit_task(self.edit_index, task_data)
        else:
            self.service.add_task(task_data)

        self.edit_mode = False
        self.edit_index = None
        self.task_input.clear()
        self.refresh_tasks()

        self.show_message("Công việc đã được lưu", color="#4CAF50")

    def highlight_edit_row(self, row):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if i == row:
                item.setBackground(Qt.white)
                item.setForeground(QColor("red"))
            else:
                item.setBackground(Qt.lightGray)
                item.setForeground(Qt.gray)
                
    # ĐỂ làm mờ`các widget khác khi đang sửa`
    def set_edit_mode(self, editing=True):
        """
        Khi editing=True: disable các widget khác, chỉ để widget đang edit active
        Khi editing=False: enable lại tất cả
        """
        # Danh sách widget cần disable khi edit
        widgets_to_toggle = [
            self.search_input,
            self.filter_done,
            self.filter_sent,
            self.filter_pending,
            self.list_widget,
        
            # ... thêm các widget khác nếu cần
        ]
        widgets_to_toggle = [w for w in widgets_to_toggle if w not in [
            self.task_input, self.start_date, self.due_date, self.deadline_input
        ]]

        for w in widgets_to_toggle:
            w.setEnabled(not editing)  # disable khi edit, enable khi xong
            if editing:
                w.setStyleSheet("background-color: #f0f0f0; color: #a0a0a0;")
            else:
                w.setStyleSheet("")  # trở về mặc định
    # ĐỂ SỬA CÔNG VIỆC

    def edit_task(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return

        task = self.filtered_tasks[row]

        self.task_input.setText(task["title"])
        self.start_date.setDate(QDate.fromString(task["start_date"], "yyyy-MM-dd"))
        self.due_date.setDate(QDate.fromString(task["due_date"], "yyyy-MM-dd"))
        self.deadline_input.setDate(QDate.fromString(task["deadline"], "yyyy-MM-dd"))

        self.edit_mode = True
        self.edit_index = task["_fb_index"]   # 🔥 Firebase index
        self.edit_task_id = task["id"]        # 🔥 logic id

        self.highlight_edit_row(row)


    # XÓA CÔNG VIỆC
    def delete_task(self):
        row = self.list_widget.currentRow()
        if row < 0:
            self.show_message("Vui lòng chọn công việc để xóa", color="#f44336")
            return

        task = self.filtered_tasks[row]

        confirm = QMessageBox.question(
            self, "Xác nhận",
            f"Xóa công việc: {task['title']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.service.delete_task(task["id"])
            self.refresh_tasks()
    
    # ĐÁNH DẤU TRẠNG THÁI
    def mark_done(self):
        self._mark_status("done", "✅ Đã hoàn thành", "#4CAF50")

    def mark_sent(self):
        self._mark_status("sent", "📨 Đã gửi", "#FF9800")

    def mark_doing(self):
        self._mark_status("doing", "⏳ Đang làm", "#2196F3")
        
    def _mark_status(self, status, msg, color):
        row = self.list_widget.currentRow()
        if row < 0:
            return

        task = self.filtered_tasks[row]
        fb_index = task["_fb_index"]

        self.service.edit_task(fb_index, {
            "status": status,
            "edited_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        self.refresh_tasks()
        self.show_message(msg, color=color)





    def handleBrowseEmail(self):
        """Khi bấm nút Duyệt email → khởi động thread tải email"""
        self.progress = QProgressDialog("Đang tải email...", "Hủy", 0, 0, self)
        self.progress.setWindowTitle("Duyệt Email")
        self.progress.setCancelButtonText("Hủy")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        # --- Khởi tạo thread ---
        self.email_thread = EmailLoaderThread(
            self.service.email, 
            self.service.password, 
            self.service.ews_url
        )

        # --- Gắn signal ---
        self.email_thread.progress.connect(self.progress.setLabelText)
        self.email_thread.finished.connect(lambda messages: self._on_email_finished(messages))
        self.email_thread.error.connect(lambda e: QMessageBox.warning(self, "Lỗi", e))

        # Khi nhấn Hủy
        self.progress.canceled.connect(self.email_thread.cancel)

        # --- Chạy ---
        self.email_thread.start()
        
    def on_escape_pressed(self):
        if self.edit_mode:
            self.edit_mode = False
            self.edit_index = None
            self.task_input.clear()
                

    def show_message(self, text, color="#2196F3", duration=3000):
        """Hiển thị toast nhỏ ở dưới cùng"""
        self.info_label.setText(text)
        self.info_label.setStyleSheet(f"background-color:{color};color:white;padding:8px 16px;border-radius:8px;font-weight:600;")
        self.info_label.setVisible(True)

        QTimer.singleShot(duration, lambda: self.info_label.setVisible(False))
    
    
    def _on_email_finished(self, messages):
        self.progress.close()
        show_email_dialog(self, messages)  # truyền self làm parent

   