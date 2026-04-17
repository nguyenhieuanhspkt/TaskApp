import sys
# Import đầy đủ các class cần thiết từ QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QFrame, QScrollArea, QLabel, QApplication
)
from PyQt5.QtCore import Qt

# Import các module của bạn
from ui.task_manager_widget import TaskManager

# ✅ Import AI widget (module 1 file)
# Đảm bảo file ai_csv_chat_widget.py nằm trong PYTHONPATH (cùng thư mục main hoặc đã add vào sys.path)
try:
    from ai_csv_chat_widget import AIAnalysisWidget
except ImportError as e:
    AIAnalysisWidget = None
    print("⚠️ Không tìm thấy ai_csv_chat_widget.AIAnalysisWidget. "
          "Hãy chắc chắn file ai_csv_chat_widget.py nằm trong project. Lỗi:", e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý & Phân tích - Tổ Thẩm định")
        self.resize(1200, 800)

        # 1. Widget trung tâm và Layout chính (Ngang)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 2. Thanh điều hướng bên trái
        self.create_navigator()

        # 3. Khu vực nội dung bên phải (Dùng QStackedWidget để chuyển module)
        self.content_stack = QStackedWidget()

        # --- MODULE 1: QUẢN LÝ TASK ---
        self.scroll_task = QScrollArea()
        self.scroll_task.setWidgetResizable(True)
        self.task_manager = TaskManager()
        self.scroll_task.setWidget(self.task_manager)

        # --- MODULE 2: AI ANALYSIS ---
        if AIAnalysisWidget is not None:
            # Nhúng widget AI thực tế
            self.ai_widget = AIAnalysisWidget()
        else:
            # Fallback trang trống khi chưa có module AI
            self.ai_widget = QWidget()
            ai_layout = QVBoxLayout(self.ai_widget)
            ai_label = QLabel("🤖 Không tải được Trợ lý AI. Kiểm tra import ai_csv_chat_widget.py")
            ai_label.setAlignment(Qt.AlignCenter)
            ai_layout.addWidget(ai_label)

        # Thêm các module vào Stack
        self.content_stack.addWidget(self.scroll_task)  # Index 0
        self.content_stack.addWidget(self.ai_widget)    # Index 1

        # 4. Gom tất cả vào Layout chính
        self.main_layout.addWidget(self.nav_frame)
        self.main_layout.addWidget(self.content_stack)

    def create_navigator(self):
        """Tạo thanh menu bên trái"""
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(200)
        self.nav_frame.setStyleSheet("""
            QFrame { background-color: #2c3e50; border: none; }
            QPushButton {
                color: white; border: none; padding: 15px;
                text-align: left; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton#active { background-color: #1abc9c; border-left: 5px solid #ecf0f1; }
        """)

        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setAlignment(Qt.AlignTop)

        # Tạo nút bấm
        self.btn_tasks = QPushButton("📋 Quản lý Hồ sơ")
        self.btn_ai = QPushButton("🤖 Trợ lý AI")

        # Gán sự kiện
        self.btn_tasks.clicked.connect(lambda: self.switch_page(0))
        self.btn_ai.clicked.connect(lambda: self.switch_page(1))

        nav_layout.addWidget(self.btn_tasks)
        nav_layout.addWidget(self.btn_ai)

        # Set nút mặc định là active
        self.btn_tasks.setObjectName("active")

    def switch_page(self, index):
        """Hàm chuyển đổi giữa các module"""
        self.content_stack.setCurrentIndex(index)

        # Cập nhật hiệu ứng nút active (nút nào đang chọn thì sáng lên)
        self.btn_tasks.setObjectName("active" if index == 0 else "")
        self.btn_ai.setObjectName("active" if index == 1 else "")

        # Ép PyQt5 cập nhật lại Style ngay lập tức
        self.btn_tasks.style().unpolish(self.btn_tasks)
        self.btn_tasks.style().polish(self.btn_tasks)
        self.btn_ai.style().unpolish(self.btn_ai)
        self.btn_ai.style().polish(self.btn_ai)


