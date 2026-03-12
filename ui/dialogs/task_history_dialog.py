from PyQt5.QtWidgets import *


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