import os
import subprocess
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFrame, QLabel, 
                             QComboBox, QPushButton, QGraphicsDropShadowEffect,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon

from config import USER_PATHS
from utils import resource_path

class WelcomeUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_path = None
        self.setFixedSize(550, 600)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- CONTAINER CHÍNH ---
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 40px;
            }
        """)
        
        # Hiệu ứng bóng đổ cho cả khung App
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(40, 50, 40, 50)
        c_layout.setSpacing(15)

        # 1. LOGO
        self.logo = QLabel()
        logo_file = resource_path("logo.png")
        if os.path.exists(logo_file):
            pixmap = QPixmap(logo_file)
            self.logo.setPixmap(pixmap.scaled(420, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setText("APPRAISAL TEAM\nTỔ THẨM ĐỊNH")
            self.logo.setStyleSheet("font-size: 26px; font-weight: bold; color: #003399;")
        c_layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        # 2. TIÊU ĐỀ
        title_lbl = QLabel("HỆ THỐNG QUẢN LÝ HỒ SƠ 2026")
        title_lbl.setStyleSheet("""
            color: #2d3436; 
            font-size: 17px; 
            font-weight: 800; 
            letter-spacing: 1px;
            margin-bottom: 5px;
        """)
        c_layout.addWidget(title_lbl, alignment=Qt.AlignCenter)

        # 3. COMBOBOX (Đã làm đẹp lại phần UI/UX)
        self.combo = QComboBox()
        self.combo.addItems(USER_PATHS.keys())
        self.combo.setCursor(Qt.PointingHandCursor)
        
        # Cấu hình để menu đổ xuống có thể bo góc
        self.combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
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
            QComboBox:hover {
                border: 2px solid #003399;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 40px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 2px solid #2f3542;
                border-bottom: 2px solid #2f3542;
                width: 8px;
                height: 8px;
                margin-top: -4px;
                margin-right: 20px;
            }
            /* Định dạng danh sách xổ xuống */
            QAbstractItemView {
                background-color: white;
                border: 1px solid #dcdde1;
                selection-background-color: #003399;
                selection-color: white;
                outline: none;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        c_layout.addWidget(self.combo)

        # 4. NHÃN BÁO LỖI (Quan trọng để báo OneDrive)
        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setMinimumHeight(40)
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setStyleSheet("color: #eb4d4b; font-size: 13px; font-weight: 600;")
        c_layout.addWidget(self.error_lbl)

        # 5. NÚT START
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
            QPushButton:hover { background-color: #002570; }
            QPushButton:pressed { background-color: #001b52; padding-top: 5px; }
        """)
        self.btn_ok.clicked.connect(self.validate_and_start)
        c_layout.addWidget(self.btn_ok)

        # 6. FOOTER
        footer_lbl = QLabel("© 2026 Appraisal Team - EVN\nVersion 02.02.2026")
        footer_lbl.setStyleSheet("color: #a4b0be; font-size: 11px;")
        footer_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(footer_lbl)

        layout.addWidget(self.container)

    def is_onedrive_running(self):
        """Kiểm tra tiến trình OneDrive.exe có đang chạy ẩn không"""
        try:
            # Dùng tasklist để quét tiến trình, ẩn cửa sổ CMD đen
            cmd = 'tasklist /FI "IMAGENAME eq OneDrive.exe"'
            output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode('utf-8', errors='ignore')
            return "OneDrive.exe" in output
        except Exception:
            return False

    def validate_and_start(self):
        # Bước 1: Bắt buộc mở OneDrive
        if not self.is_onedrive_running():
            self.error_lbl.setText("❌ LỖI: OneDrive chưa chạy!\nVui lòng mở OneDrive để tránh mất dữ liệu, nhớ chờ vài phút cho onedrive synchro.")
            return

        # Bước 2: Kiểm tra thư mục dữ liệu
        user_key = self.combo.currentText()
        path = USER_PATHS.get(user_key)
        
        if path and os.path.exists(path):
            self.selected_path = path
            self.accept() # Đóng dialog và trả về kết quả True cho main.py
        else:
            self.error_lbl.setText(f"⚠️ Không tìm thấy thư mục của {user_key}!\nKiểm tra lại kết nối OneDrive.")