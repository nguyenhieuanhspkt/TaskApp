import sys
import os, re
import json
import getpass
from datetime import datetime
from PyQt5.QtCore import Qt


# import psutil  # thêm ở đầu file

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLineEdit, QDateEdit,
    QMessageBox, QLabel,QRadioButton, QButtonGroup,QShortcut,QListWidgetItem,QGraphicsOpacityEffect

)
from PyQt5.QtCore import QDate, QTimer, Qt, QSize, QPropertyAnimation

from PyQt5.QtGui import QKeySequence


# ✅ Đường dẫn file JSON lưu trên OneDrive
FILE_PATH = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\TaskApp\tasks.json"
BASE_FOLDER = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định"




class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Team Task Manager (OneDrive Sync)")
        self.resize(680, 550)
        self.tasks = []
        self.last_mod_time = 0
        self.current_user = getpass.getuser()
        self.edit_mode = False
        self.edit_index = None

        self.load_tasks()
        self.init_ui()
        self.setup_auto_refresh()
        
    def init_ui(self):
        layout = QVBoxLayout()

        # --- Thanh tìm kiếm ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_input.textChanged.connect(self.update_list)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Shortcut: Ctrl+F để focus tìm kiếm, ESC để thoát
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
     

        # --- Ngày nhận / Hẹn / Deadline ---
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("📅 Ngày nhận:"))
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("🎯 Ngày hẹn HT:"))
        self.due_date = QDateEdit(calendarPopup=True)
        self.due_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.due_date)

        date_layout.addWidget(QLabel("⏰ Deadline:"))
        self.deadline_input = QDateEdit(calendarPopup=True)
        self.deadline_input.setDate(QDate.currentDate())
        date_layout.addWidget(self.deadline_input)
        layout.addLayout(date_layout)

        # --- Các nút thao tác ---
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Thêm / Lưu")
        add_btn.clicked.connect(self.add_or_edit_task)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Sửa")
        edit_btn.clicked.connect(self.edit_task)
        btn_layout.addWidget(edit_btn)
        # --- Nút trạng thái ---
        doing_btn = QPushButton("⏳ Đang làm")
        doing_btn.clicked.connect(self.mark_doing)
        doing_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        btn_layout.addWidget(doing_btn)

        sent_btn = QPushButton("📨 Đã gửi")
        sent_btn.clicked.connect(self.mark_sent)
        sent_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        btn_layout.addWidget(sent_btn)

        done_btn = QPushButton("✅ Hoàn thành")
        done_btn.clicked.connect(self.mark_done)
        done_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_layout.addWidget(done_btn)

        delete_btn = QPushButton("🗑️ Xóa")
        delete_btn.clicked.connect(self.delete_task)
        btn_layout.addWidget(delete_btn)

        open_btn = QPushButton("📂 Mở folder")
        open_btn.clicked.connect(self.open_folder)
        btn_layout.addWidget(open_btn)

        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.clicked.connect(self.load_tasks)
        btn_layout.addWidget(refresh_btn)

        layout.addLayout(btn_layout)

        # --- Danh sách công việc ---
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.open_folder)
        layout.addWidget(self.list_widget)

        # --- Bộ lọc trạng thái ---
        filter_layout = QHBoxLayout()
        self.filter_all = QRadioButton("Tất cả")
        self.filter_pending = QRadioButton("Đang làm ⏳")
        self.filter_sent = QRadioButton("Đã gửi 📨")
        self.filter_done = QRadioButton("Đã hoàn thành ✅")

        self.filter_all.setChecked(True)

        filter_layout.addWidget(QLabel("Lọc:"))
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_pending)
        filter_layout.addWidget(self.filter_sent)
        filter_layout.addWidget(self.filter_done)
        layout.addLayout(filter_layout)

        # Gom nhóm radio
        self.filter_group = QButtonGroup()
        for rb in [self.filter_all, self.filter_pending, self.filter_sent, self.filter_done]:
            self.filter_group.addButton(rb)
            rb.toggled.connect(self.update_list)

        self.setLayout(layout)

        # --- Floating toast label ---
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("""
            background-color: rgba(50, 50, 50, 180);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setVisible(False)
        self.info_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.info_label)

        # Khởi tạo danh sách lần đầu
        self.update_list()


    # -------------------------- #
    #      Chức năng chính       #
    # -------------------------- #
    def resizeEvent(self, event):
        if self.info_label.isVisible():
            x = (self.width() - self.info_label.width()) // 2
            y = self.height() - self.info_label.height() - 20
            self.info_label.move(x, y)
        super().resizeEvent(event)

    def setup_auto_refresh(self):
        """Tự động làm mới mỗi 30 giây"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_tasks)
        self.timer.start(30 * 1000)
    def on_escape_pressed(self):
        # Nếu đang ở chế độ sửa task
        if self.edit_mode:
            self.edit_mode = False
            self.edit_index = None
            self.task_input.clear()
            # reset các date input về ngày hiện tại
            self.start_date.setDate(QDate.currentDate())
            self.due_date.setDate(QDate.currentDate())
            self.deadline_input.setDate(QDate.currentDate())
            QMessageBox.information(self, "Hủy chỉnh sửa", "Chế độ sửa đã bị hủy.")
        else:
            # Bỏ focus khỏi input (search hoặc task_input)
            focused_widget = self.focusWidget()
            if focused_widget:
                focused_widget.clearFocus()
            # ListWidget nhận focus
            self.list_widget.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        current_row = self.list_widget.currentRow()
        count = self.list_widget.count()

        # ---------------- Up / Down ----------------
        if key in (Qt.Key_Up, Qt.Key_Down):
            # Bỏ focus search input nếu có
            self.search_input.clearFocus()
            self.list_widget.setFocus()

            if key == Qt.Key_Up and current_row > 0:
                self.list_widget.setCurrentRow(current_row - 1)
            elif key == Qt.Key_Down and current_row < count - 1:
                self.list_widget.setCurrentRow(current_row + 1)
            event.accept()

        # ---------------- Enter ----------------
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if current_row >= 0:
                self.list_widget.setCurrentRow(current_row)
                self.open_folder()
            event.accept()

        # ---------------- Ctrlt+S ----------------
        elif key == Qt.Key_S and modifiers & Qt.ControlModifier:
            if current_row >= 0:
                self.list_widget.setCurrentRow(current_row)
                self.edit_task()
            event.accept()

        # ---------------- Ctrl+W ----------------
        elif key == Qt.Key_W and modifiers & Qt.ControlModifier:
            self.close()
            event.accept()

        # ---------------- Escape ----------------
        elif key == Qt.Key_Escape:
            self.on_escape_pressed()
            event.accept()
            # ---------------- ctrl+L to save ----------------
        elif key == Qt.Key_L and modifiers & Qt.ControlModifier:
            # Ctrl+L → lưu task (thêm hoặc lưu nếu đang edit)
            self.add_or_edit_task()
            event.accept()

        else:
            super().keyPressEvent(event)
    def show_message(self, msg, duration=2500, color="#4CAF50"):
        """Hiển thị thông báo (toast) ở dưới, giữ duration ms rồi fade out."""
        # --- cập nhật màu và nội dung ---
        self.info_label.setText(msg)
        self.info_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 8px;
        """)
        self.info_label.adjustSize()

        # đặt vị trí giữa dưới cùng
        x = (self.width() - self.info_label.width()) // 2
        y = self.height() - self.info_label.height() - 20
        self.info_label.move(x, y)

        self.info_label.show()
        self.info_label.raise_()

        # tạo effect opacity
        effect = QGraphicsOpacityEffect(self.info_label)
        self.info_label.setGraphicsEffect(effect)
        effect.setOpacity(1.0)

        # nếu có animation cũ, dừng nó
        if hasattr(self, "_anim") and self._anim is not None:
            try:
                self._anim.stop()
            except Exception:
                pass

        # tạo animation fade-out (1s)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(1000)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)

        # sau `duration` ms mới bắt đầu fade-out
        QTimer.singleShot(duration, anim.start)

        # khi kết thúc, ẩn label
        anim.finished.connect(lambda: self.info_label.hide())

        # giữ tham chiếu tránh GC
        self._anim = anim







    def load_tasks(self):
        try:
            if os.path.exists(FILE_PATH):
                mod_time = os.path.getmtime(FILE_PATH)
                if mod_time != self.last_mod_time:
                    with open(FILE_PATH, "r", encoding="utf-8") as f:
                        self.tasks = json.load(f)
                    self.last_mod_time = mod_time
                    self.update_list()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải file: {e}")

    def save_tasks(self):
        try:
            os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
            self.last_mod_time = os.path.getmtime(FILE_PATH)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lưu thất bại: {e}")

    # -------------------------- #
    #     Thêm / Sửa Task        #
    # -------------------------- #
  

    def add_or_edit_task(self):
        import psutil
        title = self.task_input.text().strip()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        due_date = self.due_date.date().toString("yyyy-MM-dd")
        deadline = self.deadline_input.date().toString("yyyy-MM-dd")

        if not title:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên công việc!")
            return

        # --- Giữ focus lại cho dòng đang edit ---
        current_row = self.list_widget.currentRow()

        if self.edit_mode:
            # 🔹 Chỉnh sửa task
            t = self.tasks[self.edit_index]
            t["title"] = title
            t["start_date"] = start_date
            t["due_date"] = due_date
            t["deadline"] = deadline
            t["edited_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.edit_mode = False
            self.edit_index = None
            self.show_message("Đã lưu thay đổi công việc!", color="#4CAF50")  # xanh lá

        else:
            # 🔹 Thêm task mới
            if not any(p.name() == "OneDrive.exe" for p in psutil.process_iter()):
                QMessageBox.warning(self, "Lỗi", "OneDrive chưa chạy! Vui lòng khởi động OneDrive.")
                return

            # Tạo id mới
            existing_folders = os.listdir(BASE_FOLDER)
            ids_in_folder = []
            for f in existing_folders:
                m = re.match(r"Thẩm định (\d+)", f)
                if m:
                    ids_in_folder.append(int(m.group(1)))

            max_id_folder = max(ids_in_folder) if ids_in_folder else 0
            print(max_id_folder)
            max_id_json = max((task.get("id", 0) for task in self.tasks), default=0)
            new_id = max(max_id_folder, max_id_json) + 1

            # Tạo folder
            folder_name = f"Thẩm định {new_id}"
            folder_path = os.path.join(BASE_FOLDER, folder_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể tạo folder: {e}")
                return

            # Tạo task mới
            new_task = {
                "id": new_id,
                "folder": folder_name,
                "title": title,
                "start_date": start_date,
                "due_date": due_date,
                "deadline": deadline,
                "status": "doing",  # 🆕 Trạng thái mặc định
                "author": self.current_user,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "edited_at": ""
            }
            self.tasks.append(new_task)
            self.show_message(f"Đã thêm công việc mới: {title}", color="#2196F3")  # xanh dương

        # --- Lưu và cập nhật ---
        self.save_tasks()
        self.update_list()

        # --- Giữ focus ---
        if current_row >= 0 and current_row < self.list_widget.count():
            self.list_widget.setCurrentRow(current_row)
            self.list_widget.setFocus()

        self.task_input.clear()


    def edit_task(self):
        selected = self.list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Chú ý", "Chọn công việc để sửa!")
            return

        task_to_edit = self.filtered_tasks[selected]

        try:
            real_index = self.tasks.index(task_to_edit)
        except ValueError:
            # Nếu folder cũ chưa có JSON, thêm vào
            self.tasks.append(task_to_edit)
            real_index = len(self.tasks) - 1

        # Điền dữ liệu vào UI
        self.task_input.setText(task_to_edit.get("title", ""))
        self.start_date.setDate(QDate.fromString(task_to_edit.get("start_date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        self.due_date.setDate(QDate.fromString(task_to_edit.get("due_date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        self.deadline_input.setDate(QDate.fromString(task_to_edit.get("deadline", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))

        self.edit_mode = True
        self.edit_index = real_index

        self.show_message("✏️ Đang chỉnh sửa — nhấn Ctrl+L để lưu thay đổi.", color="#2196F3")


    def delete_task(self):
        selected = self.list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Chú ý", "Chọn công việc để xóa!")
            return

        task_to_delete = self.filtered_tasks[selected]

        try:
            real_index = self.tasks.index(task_to_delete)
        except ValueError:
            # Task không có trong JSON, không xóa JSON
            real_index = None

        folder_name = task_to_delete.get("folder", "")
        folder_path = os.path.join(BASE_FOLDER, folder_name)

        confirm = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có chắc muốn xóa công việc: {task_to_delete.get('title','')}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Xóa khỏi JSON nếu có
            if real_index is not None:
                self.tasks.pop(real_index)
                self.save_tasks()

            self.update_list()

            # Rename folder nếu tồn tại
            if os.path.exists(folder_path):
                new_folder_name = folder_name + "_đã xóa"
                new_folder_path = os.path.join(BASE_FOLDER, new_folder_name)
                try:
                    os.rename(folder_path, new_folder_path)
                    self.show_message(
                        f"Đã đổi tên thành: {new_folder_name}. Bạn có thể xóa thủ công sau!",
                        color="#F44336"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Lỗi", f"Không thể rename folder: {e}")


    def mark_done(self):
        current_row = self.list_widget.currentRow()
        if current_row < 0 or current_row >= len(self.filtered_tasks):
            self.show_message("Chưa chọn công việc nào!", color="#F44336")
            return

        task = self.filtered_tasks[current_row]
        index_in_all = next((i for i, t in enumerate(self.tasks) if t["id"] == task["id"]), None)
        if index_in_all is None:
            return

        self.tasks[index_in_all]["status"] = "done"
        self.tasks[index_in_all]["edited_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.save_tasks()
        self.update_list()
        self.show_message("Đã hoàn thành công việc!", color="#4CAF50")

        
    def mark_doing(self):
        """Đặt task về trạng thái đang làm"""
        selected = self.list_widget.currentRow()
        if selected < 0:
            self.show_message("Chọn công việc để đánh dấu!", color="#F44336")
            return

        task = self.filtered_tasks[selected]
        task["status"] = "doing"
        self.save_tasks()
        self.update_list()
        self.show_message("Công việc đã chuyển sang trạng thái ⏳ Đang làm", color="#2196F3")


    def mark_sent(self):
        """Đánh dấu công việc đã gửi"""
        selected = self.list_widget.currentRow()
        if selected < 0:
            self.show_message("Chọn công việc để đánh dấu!", color="#F44336")
            return

        task = self.filtered_tasks[selected]
        task["status"] = "sent"
        self.save_tasks()
        self.update_list()
        self.show_message("Công việc đã chuyển sang trạng thái 📨 Đã gửi", color="#FF9800")

    def update_list(self):
        if not hasattr(self, "list_widget"):
            return

        self.list_widget.clear()

        # --- Lọc theo trạng thái ---
        if self.filter_done.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t.get("status") == "done"]
        elif self.filter_sent.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t.get("status") == "sent"]
        elif self.filter_pending.isChecked():
            self.filtered_tasks = [t for t in self.tasks if t.get("status") == "doing"]
        else:
            self.filtered_tasks = self.tasks.copy()


        # --- Lọc theo tìm kiếm ---
        query = self.search_input.text().strip().lower()
        if query:
            self.filtered_tasks = [
                t for t in self.filtered_tasks
                if query in t.get("title", "").lower()
                or query in t.get("folder", "").lower()
                or query in t.get("description", "").lower()
            ]

        # --- Sắp xếp theo deadline ---
        self.filtered_tasks.sort(key=lambda x: x.get("deadline", "9999-12-31"))

        # --- Hiển thị lên list_widget ---
        # --- Hiển thị lên list_widget ---
        for t in self.filtered_tasks:
            # Lấy trạng thái công việc
            status_value = t.get("status", "pending")  # Mặc định: đang làm

            # Chọn icon tương ứng
            if status_value == "done":
                status = "✅"
            elif status_value == "sent":
                status = "📤"  # icon gửi
            else:
                status = "⏳"  # đang làm

            author = t.get("author", "Không rõ")
            folder = t.get("folder", "Chưa có folder")
            edited = f" (sửa {t['edited_at']})" if t.get("edited_at") else ""

            # HTML hiển thị rõ ràng
            html_text = (
                f"{status} <b>[{folder}]</b> {t['title']}<br>"
                f"📅 Nhận: {t.get('start_date','')} | 🎯 Hẹn: {t.get('due_date','')} | ⏰ DL: {t.get('deadline','')} — {author}{edited}"
            )

            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 50))

            label = QLabel()
            label.setText(html_text)
            label.setWordWrap(True)
            label.setTextFormat(Qt.RichText)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)



    def open_folder(self):
        import subprocess
        selected = self.list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Chú ý", "Chọn công việc để mở folder!")
            return

        task = self.filtered_tasks[selected]  # <-- Dùng filtered_tasks thay vì self.tasks
        folder_name = task.get("folder")
        if not folder_name:
            QMessageBox.warning(self, "Lỗi", "Task này chưa có folder!")
            return

        folder_path = os.path.join(BASE_FOLDER, folder_name)
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, "Lỗi", f"Folder không tồn tại: {folder_path}")
            return

        subprocess.Popen(f'explorer "{folder_path}"')

# -------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManager()
    window.show()
    sys.exit(app.exec_())
