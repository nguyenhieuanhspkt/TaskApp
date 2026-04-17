import sys
from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Class đại diện cho một "Thẻ bài công cụ"
class ToolCard(QFrame):
    clicked = pyqtSignal(str)  # Tín hiệu khi bấm vào thẻ

    def __init__(self, title, description, color, tool_id):
        super().__init__()
        self.tool_id = tool_id
        self.setFixedSize(200, 150)
        self.setCursor(Qt.PointingHandCursor)
        
        # Style cho thẻ bài (Card)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 2px solid #E0E0E0;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background-color: #F9F9F9;
            }}
        """)

        layout = QVBoxLayout()
        
        # Tiêu đề thẻ
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {color}; border: none;")
        self.title_label.setWordWrap(True)
        
        # Mô tả ngắn
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Arial", 9))
        self.desc_label.setStyleSheet("color: #7F8C8D; border: none;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignTop)

        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self.tool_id)

# Cửa sổ chính AI Hub
class AIWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Tool Hub - TaskApp")
        self.resize(750, 500)
        self.setStyleSheet("background-color: #F0F2F5;") # Màu nền mặt bàn
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Tiêu đề Hub
        header = QLabel("Hệ sinh thái AI - Tổ Thẩm định")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2C3E50; margin: 10px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Khu vực chứa các thẻ (Scroll Area để cuộn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(30, 20, 30, 20)

        # DANH SÁCH CÁC CÔNG CỤ (Anh có thể thêm mới ở đây)
        self.tools = [
            ("Dịch thuật AI", "Dịch thuật hồ sơ kỹ thuật chuyên ngành.", "#E67E22", "translator"),
            ("Tra cứu Vật tư", "Tìm kiếm vật tư thông minh bằng AI.", "#3498DB", "vattu_search"),
            ("Tóm tắt Hồ sơ", "Trích xuất ý chính từ file thầu dài.", "#27AE60", "summarizer"),
            ("Kiểm tra Đơn giá", "So sánh đơn giá với dữ liệu quá khứ.", "#E74C3C", "price_check"),
        ]

        self.render_cards()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def render_cards(self):
        # Xếp các thẻ vào lưới (3 cột)
        col_count = 3
        for index, (name, desc, color, tid) in enumerate(self.tools):
            card = ToolCard(name, desc, color, tid)
            card.clicked.connect(self.open_tool)
            row = index // col_count
            col = index % col_count
            self.grid_layout.addWidget(card, row, col)

    def open_tool(self, tool_id):
        # Hàm điều hướng khi bấm vào từng thẻ
        print(f"Đang mở công cụ: {tool_id}")
        if tool_id == "translator":
            # logic mở translator tại đây
            pass
        elif tool_id == "vattu_search":
            # logic mở tra cứu tại đây
            pass