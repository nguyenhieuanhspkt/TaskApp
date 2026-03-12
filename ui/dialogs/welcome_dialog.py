from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
import os

from config import USER_PATHS
from utils import resource_path

class WelcomeUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(550, 600)  # Kích thước rộng rãi hơn để giống ảnh mẫu
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Khung chứa chính (Container) với hiệu ứng bo góc và bóng đổ chuyên nghiệp
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 40px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(40, 50, 40, 50)
        c_layout.setSpacing(20)

        # 1. LOGO - Đưa vào một khung có nền xanh nhẹ nếu cần hoặc để trần như ảnh
        self.logo = QLabel()
        logo_file = resource_path("logo.png")
        if os.path.exists(logo_file):
            pixmap = QPixmap(logo_file)
            self.logo.setPixmap(pixmap.scaled(420, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setText("APPRAISAL TEAM\nTỔ THẨM ĐỊNH")
            self.logo.setStyleSheet("font-size: 28px; font-weight: bold; color: #003399;")
        c_layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        c_layout.addSpacing(10)

        # 2. TITLE - Chữ in đậm màu đen xám
        title_lbl = QLabel("HỆ THỐNG QUẢN LÝ HỒ SƠ 2026")
        title_lbl.setStyleSheet("""
            color: #2d3436; 
            font-size: 18px; 
            font-weight: 800; 
            letter-spacing: 1px;
        """)
        c_layout.addWidget(title_lbl, alignment=Qt.AlignCenter)

        # 3. COMBOBOX - Thiết kế tối giản, hiện đại
        self.combo = QComboBox()
        self.combo.addItems(USER_PATHS.keys())
        self.combo.setCursor(Qt.PointingHandCursor)
        self.combo.setStyleSheet("""
            QComboBox {
                height: 55px; 
                border-radius: 15px; 
                border: 2px solid #f1f2f6; 
                background-color: #f8f9fa;
                padding-left: 20px;
                font-size: 16px;
                color: #2f3542;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                image: none; /* Bạn có thể thêm icon mũi tên ở đây */
            }
            QComboBox:hover {
                border: 2px solid #003399;
            }
        """)
        c_layout.addWidget(self.combo)

        # 4. ERROR LABEL
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ff4757; font-size: 12px; font-weight: 500;")
        c_layout.addWidget(self.error_lbl, alignment=Qt.AlignCenter)

        # 5. BUTTON OK - Xanh đậm EVN, hiệu ứng nhấn
        self.btn_ok = QPushButton("BẮT ĐẦU LÀM VIỆC")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #003399; 
                color: white; 
                height: 60px; 
                border-radius: 20px; 
                font-size: 18px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #002570;
            }
            QPushButton:pressed {
                background-color: #001b52;
                padding-top: 5px;
            }
        """)
        self.btn_ok.clicked.connect(self.validate_and_start)
        c_layout.addWidget(self.btn_ok)

        # 6. FOOTER - Thông tin bản quyền nhỏ bên dưới (như ảnh mẫu)
        footer_lbl = QLabel("© 2026 Appraisal Team - EVN\nVersion 02.02.2026")
        footer_lbl.setStyleSheet("color: #a4b0be; font-size: 11px;")
        footer_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(footer_lbl)

        layout.addWidget(self.container)

    def validate_and_start(self):
        path = USER_PATHS.get(self.combo.currentText())
        if path and os.path.exists(path):
            self.selected_path = path
            self.accept()
        else:
            self.error_lbl.setText("⚠ Không tìm thấy thư mục người dùng!")