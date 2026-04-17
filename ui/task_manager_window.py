from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox
from ui.task_manager_widget import TaskManagerWidget

class TaskManagerWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskApp - Quản lý công việc")
        self.resize(800, 600)

        # Gắn widget quản lý task vào cửa sổ
        self.task_widget = TaskManagerWidget(self)
        self.setCentralWidget(self.task_widget)

        # Tạo menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        refresh_action = QAction("Làm mới", self)
        refresh_action.triggered.connect(self.task_widget.load_tasks)
        file_menu.addAction(refresh_action)

    def closeEvent(self, event):
        QMessageBox.information(self, "Thoát", "Đang thoát ứng dụng...")
        event.accept()
