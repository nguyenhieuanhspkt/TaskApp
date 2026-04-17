

class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskApp - Quản lý công việc Tổ thẩm định")
        self.resize(680, 550)
        self.tasks = []
        self.last_sha = None
        self.current_user = getpass.getuser()
        self.edit_mode = False
        self.edit_index = None

        self.load_tasks()
        self.init_ui()
        self.setup_auto_refresh()

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
        self.task_input.returnPressed.connect(self.add_or_edit_task)
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
            ("➕ Thêm / Lưu", self.add_or_edit_task, None),
            ("✏️ Sửa", self.edit_task, None),
            ("⏳ Đang làm", self.mark_doing, "#2196F3"),
            ("📨 Đã gửi", self.mark_sent, "#FF9800"),
            ("✅ Hoàn thành", self.mark_done, "#4CAF50"),
            ("🗑️ Xóa", self.delete_task, None),
            ("🔄 Làm mới", self.load_tasks, None),
            ("📧 Duyệt Email", self.browse_email, None),
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
        self.update_list()
    # ---------------- AUTO REFRESH ----------------
    def setup_auto_refresh(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_tasks)
        self.timer.start(30 * 1000)

 
    # ---------------- LOAD / SAVE (firebase) ----------------
    def load_tasks(self):
        print("[DEBUG] Bắt đầu tải dữ liệu...")            # Ưu tiên lấy từ Firebase
        try:
            data = get_firebase_data()
            if data:
                # Nếu dữ liệu Firebase là dict và có "tasks"
                if isinstance(data, dict) and "tasks" in data:
                    self.tasks = data["tasks"]
                elif isinstance(data, list):
                    self.tasks = data
                else:
                    self.tasks = []
                self.show_message("✅ Đã tải dữ liệu từ Firebase", color="#43A047")
                self.update_list()
                print("[DEBUG] Tải thành công từ Firebase:", len(self.tasks), "tasks")
                return
        except Exception as fb_err:
            print("[DEBUG] Không lấy được dữ liệu từ Firebase:", fb_err)
            # Nếu lỗi, sẽ thử lấy từ GitHub như cũ


    def save_tasks(self):
        print("[DEBUG] Bắt đầu save Firebase dữ liệu...")            
        # Lưu lên Firebase trước
        try:
            from firebase_admin import db
            payload_data = {
                "schema_version": 1,
                "tasks": self.tasks
            }
            ref = db.reference('/')
            ref.set(payload_data)
            self.show_message("💾 Đã lưu dữ liệu lên Firebase", color="#43A047")
            print("[DEBUG] Lưu thành công lên Firebase")
            return
        except Exception as fb_err:
            print("[DEBUG] Không lưu được lên Firebase:", fb_err)


    # ---------------- CRUD ----------------
    def add_or_edit_task(self):
        title = self.task_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên công việc!")
            return

        start_date = self.start_date.date().toString("yyyy-MM-dd")
        due_date = self.due_date.date().toString("yyyy-MM-dd")
        deadline = self.deadline_input.date().toString("yyyy-MM-dd")

        if self.edit_mode:
            t = self.tasks[self.edit_index]
            t.update({
                "title": title,
                "start_date": start_date,
                "due_date": due_date,
                "deadline": deadline,
                "edited_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            self.edit_mode = False
            self.edit_index = None
        else:
            new_id = max([t.get("id", 0) for t in self.tasks], default=0) + 1
            new_task = {
                "id": new_id,
                "folder": f"Thẩm định {new_id}",
                "title": title,
                "start_date": start_date,
                "due_date": due_date,
                "deadline": deadline,
                "status": "doing",
                "author": self.current_user,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "edited_at": "",
            }
            self.tasks.append(new_task)
        self.save_tasks()
        self.update_list()
        self.task_input.clear()

    def edit_task(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        task = self.filtered_tasks[idx]
        real_index = self.tasks.index(task)
        self.task_input.setText(task["title"])
        self.start_date.setDate(QDate.fromString(task["start_date"], "yyyy-MM-dd"))
        self.due_date.setDate(QDate.fromString(task["due_date"], "yyyy-MM-dd"))
        self.deadline_input.setDate(QDate.fromString(task["deadline"], "yyyy-MM-dd"))
        self.edit_mode = True
        self.edit_index = real_index

    def delete_task(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        task = self.filtered_tasks[idx]
        confirm = QMessageBox.question(self, "Xác nhận", f"Xóa công việc: {task['title']}?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.tasks.remove(task)
            self.save_tasks()
            self.update_list()

    def mark_done(self):
        self._mark_status("done", "✅ Đã hoàn thành", "#4CAF50")

    def mark_sent(self):
        self._mark_status("sent", "📨 Đã gửi", "#FF9800")

    def mark_doing(self):
        self._mark_status("doing", "⏳ Đang làm", "#2196F3")
    def browse_email(self):
        MYEMAIL = os.getenv("MYEMAIL")
        MYPASSEMAIL = os.getenv("MYPASSEMAIL")
        EWS_URL = os.getenv("EWS_URL")

        if not MYEMAIL or not MYPASSEMAIL or not EWS_URL:
            QMessageBox.warning(self, "Lỗi", "Chưa cấu hình email, mật khẩu hoặc EWS_URL trong biến môi trường.")
            return

        # Progress dialog có nút Cancel
        progress = QProgressDialog("Đang load email...", "Hủy", 0, 0, self)
        progress.setWindowTitle("Loading Email")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButtonText("Hủy")
        progress.show()

        # Tạo thread
        self.email_thread = EmailLoaderThread(MYEMAIL, MYPASSEMAIL, EWS_URL)
        self.email_thread.progress.connect(lambda msg: progress.setLabelText(msg))

        # Khi thread kết thúc
        def on_finished(email_list):
            progress.close()
            if not email_list:
                QMessageBox.information(self, "Thông báo", "Không có email mới từ hoangbh@vinhtan4tpp.evn.vn")
                return
            
            # subjects = [
            #     f"{msg.subject or '(Không có tiêu đề)'} - {msg.sender.email_address if msg.sender else '(Không có sender)'} - {msg.datetime_received.strftime('%Y-%m-%d %H:%M')}"
            #     for msg in email_list
            # ]
            
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(['Subject','Sender','Date'])
            table.setRowCount(len(email_list))

            
            for row, msg in enumerate(email_list):
                table.setItem(row, 0, QTableWidgetItem(msg.subject or '(Không có tiêu đề)'))
                table.setItem(row, 1, QTableWidgetItem(msg.sender.email_address if msg.sender else '(Không có sender)'))
                table.setItem(row, 2, QTableWidgetItem(msg.datetime_received.strftime('%Y-%m-%d %H:%M')))
            table.resizeColumnsToContents()
            # ----------- Cấu hình width & auto resize -----------
            table.setColumnWidth(0, 400)  # Subject cố định
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Fixed)        # Subject cố định
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Sender auto
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Date auto
            table.resizeRowsToContents()  # auto height từng row

            # Tạo dialog
            dialog = EmailDialog(table, self)
            result = dialog.exec_() # result là 1 nếu accept, 0 nếu cancel
            if result == QDialog.Accepted and dialog.selected_item:
                msg = dialog.selected_item

         

                # Tạo ID mới
                existing_ids = [t.get("id", 0) for t in self.tasks]
                new_id = max(existing_ids + [61]) + 1

                new_task = {
                    "id": new_id,
                    "folder": f"Thẩm định {new_id}",
                    "title": msg['subject'] or "(Không có tiêu đề)",
                    "start_date": msg['date'].split()[0] if msg['date'] else "",
                    "due_date": "",
                    "deadline": "",
                    "status": "doing",
                    "author": getattr(self, "current_user", "unknown"),
                    "content": "",  # nếu chỉ có dict thì chưa có body
                    "created_at": msg['date'] or "",
                    "edited_at": "",
                }

                self.tasks.append(new_task)
                self.update_list()
                self.save_tasks()
                self.show_message("✅ Đã thêm task từ email!", color="#43A047")

        self.email_thread.finished.connect(on_finished)
        self.email_thread.error.connect(lambda e: QMessageBox.warning(self, "Lỗi", f"Lỗi khi load email:\n{e}"))

        # Cancel thread khi nhấn nút Hủy
        progress.canceled.connect(lambda: self.email_thread.cancel())

        self.email_thread.start()
    def _mark_status(self, status, msg, color):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        task = self.filtered_tasks[idx]
        for t in self.tasks:
            if t["id"] == task["id"]:
                t["status"] = status
                t["edited_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        self.save_tasks()
        self.update_list()
        self.show_message(msg, color=color)


        

    # ---------------- Hiển thị ----------------
    def update_list(self):
        if not hasattr(self, "list_widget"):
            return
        self.list_widget.clear()
        if self.filter_done.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t["status"] == "done"]
        elif self.filter_sent.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t["status"] == "sent"]
        elif self.filter_pending.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t["status"] == "doing"]
        else:
            self.filtered_tasks = self.tasks.copy()

        query = self.search_input.text().strip().lower()
        if query:
            self.filtered_tasks = [t for t in self.filtered_tasks if query in t["title"].lower()]
        self.filtered_tasks.sort(key=lambda x: x.get("deadline", "9999-12-31"))

        for t in self.filtered_tasks:
            icon = {"done": "✅", "sent": "📨", "doing": "⏳"}.get(t["status"], "❓")
            html = f"{icon} <b>[{t['folder']}]</b> {t['title']}<br>📅 {t['start_date']} → 🎯 {t['due_date']} | ⏰ {t['deadline']} — {t['author']}"
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 50))
            label = QLabel()
            label.setText(html)
            label.setWordWrap(True)
            label.setTextFormat(Qt.RichText)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)

    # ---------------- Tiện ích ----------------
    def show_message(self, msg, duration=2500, color="#4CAF50"):
            # """Hiển thị thông báo (toast) ở dưới, giữ duration ms rồi fade out."""
        if not hasattr(self, "info_label"):
            print(f"[DEBUG] show_message: info_label chưa được tạo. Nội dung: {msg}")
            return

        self.info_label.setText(msg)
        self.info_label.setStyleSheet(f"background-color:{color};color:white;padding:8px 16px;border-radius:8px;font-weight:bold;")
        self.info_label.adjustSize()
        x = (self.width() - self.info_label.width()) // 2
        y = self.height() - self.info_label.height() - 20
        self.info_label.move(x, y)
        self.info_label.show()
        effect = QGraphicsOpacityEffect(self.info_label)
        self.info_label.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(1000)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        QTimer.singleShot(duration, anim.start)
        anim.finished.connect(lambda: self.info_label.hide())

    def on_escape_pressed(self):
        if self.edit_mode:
            self.edit_mode = False
            self.edit_index = None
            self.task_input.clear()

