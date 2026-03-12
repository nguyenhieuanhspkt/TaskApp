# main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from dialogs import WelcomeUserDialog
from main_window import TaskManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # THIẾT LẬP STYLE CHUNG
    app.setStyle("Fusion")
    
    # Cài đặt Font chữ mặc định cho toàn bộ App (tránh lỗi font trên máy khác)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    # Khởi chạy màn hình chào
    welcome = WelcomeUserDialog()
    if welcome.exec_():
        # Nếu chọn người dùng thành công, mở cửa sổ chính
        # Truyền đường dẫn dữ liệu đã chọn vào TaskManager
        main_app = TaskManager(welcome.selected_path)
        main_app.show()
        sys.exit(app.exec_())
    else:
        sys.exit()