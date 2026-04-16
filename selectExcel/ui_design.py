# ui_design.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, 
    QTableWidget, QSpinBox, QHBoxLayout, QGridLayout, QScrollArea, QLineEdit,QListWidget
)
from ui_design_config import APP_TITLE

class ExcelMapperUI(QWidget):
    def __init__(self):
        super().__init__()
        self.mapping_combos = {}
        self.mapping_rows = [] # Lưu trữ các widget hàng để xóa/thêm động
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, 1100, 850)
        self.main_layout = QVBoxLayout(self)

        # --- Bước 1: Chọn File ---
        file_box = QHBoxLayout()
        self.btn_open = QPushButton('📁 Chọn file Excel')
        self.lbl_file = QLabel("Chưa chọn file")
        file_box.addWidget(self.btn_open)
        file_box.addWidget(self.lbl_file, 1)
        self.main_layout.addLayout(file_box)

        # Cấu hình Sheet & Header
        config_layout = QHBoxLayout()
        self.combo_sheet = QComboBox()
        self.spin_header = QSpinBox()
        config_layout.addWidget(QLabel("Sheet:"))
        config_layout.addWidget(self.combo_sheet, 1)
        config_layout.addWidget(QLabel("Dòng Header:"))
        config_layout.addWidget(self.spin_header)
        self.main_layout.addLayout(config_layout)

        # --- BƯỚC 2: QUẢN LÝ CỘT BAREM (THÊM/BỚT) ---
        self.main_layout.addWidget(QLabel("\n🛠 Quản lý các trường dữ liệu (Barem):"))
        
        add_col_layout = QHBoxLayout()
        self.txt_new_col = QLineEdit()
        self.txt_new_col.setPlaceholderText("Nhập tên cột mới tại đây...")
        self.btn_add_col = QPushButton("➕ Thêm cột")
        self.btn_add_col.setStyleSheet("background-color: #3498db; color: white;")
        add_col_layout.addWidget(self.txt_new_col)
        add_col_layout.addWidget(self.btn_add_col)
        self.main_layout.addLayout(add_col_layout)

        # Khu vực hiển thị Mapping (Cuộn được)
        scroll = QScrollArea()
        self.scroll_content = QWidget()
        self.mapping_layout = QGridLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(350)
        self.main_layout.addWidget(scroll)

        # Tạo layout ngang để chia đôi phần dưới
        bottom_area = QHBoxLayout()

        # Cột trái: Nút Preview và Bảng Preview
        left_col = QVBoxLayout()
        self.btn_preview = QPushButton('🚀 1. XEM PREVIEW')
        self.btn_preview.setFixedHeight(40)
        self.table_preview = QTableWidget()
        left_col.addWidget(self.btn_preview)
        left_col.addWidget(self.table_preview)

        # Cột phải: Danh sách kết chuyển và nút Combine
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("📂 Danh sách chờ kết chuyển:"))
        self.list_pending = QListWidget() # Hiển thị tên file hoặc lần kết chuyển
        self.list_pending.setMaximumWidth(300)
        
        self.btn_transfer = QPushButton('➡️ 2. KẾT CHUYỂN')
        self.btn_transfer.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        
        self.btn_combine = QPushButton('💎 3. OK COMBINE (GỘP TẤT CẢ)')
        self.btn_combine.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        self.btn_combine.setFixedHeight(40)

        right_col.addWidget(self.list_pending)
        right_col.addWidget(self.btn_transfer)
        right_col.addWidget(self.btn_combine)

        bottom_area.addLayout(left_col, 7) # Chiếm 7 phần
        bottom_area.addLayout(right_col, 3) # Chiếm 3 phần
        
        self.main_layout.addLayout(bottom_area)