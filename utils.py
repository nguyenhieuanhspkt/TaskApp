# utils.py
import os, sys # Thêm sys để kiểm tra môi trường chạy
from datetime import datetime

def resource_path(relative_path):
    """ 
    Lấy đường dẫn tuyệt đối đến tài nguyên (logo, icon, thư mục module...).
    Hỗ trợ cả khi chạy code (Dev) và khi đã đóng gói (EXE) bằng PyInstaller.
    """
    if hasattr(sys, '_MEIPASS'):
        # Khi đóng gói --onefile, PyInstaller xả nén vào thư mục tạm này
        base_path = sys._MEIPASS
    else:
        # Khi chạy Dev, lấy thư mục gốc của dự án (thư mục chứa main.py)
        # Cách này an toàn hơn os.path.abspath(".") 
        base_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__ if '__main__' in sys.modules else __file__))

    return os.path.join(base_path, relative_path)

def get_weekly_path():
    """
    Hàm chuyên biệt để lấy đường dẫn folder weeklyreport.
    Giúp main_window.py luôn tìm thấy module này dù chạy ở đâu.
    """
    # Ưu tiên tìm ở ổ D nếu bạn muốn cố định, hoặc tìm theo resource_path nếu muốn đi kèm bộ cài
    path_in_bundle = resource_path("weeklyreport")
    path_fixed_d = r"d:\TaskApp_kiet\TaskApp\weeklyreport"
    
    if os.path.exists(path_in_bundle):
        return path_in_bundle
    return path_fixed_d

class AnalyticsEngine:
    """Xử lý dữ liệu thô thành các chỉ số KPI để Dashboard hiển thị"""
    
    @staticmethod
    def parse_time(log_str, year):
        """Chuyển chuỗi '31/12 09:00' thành đối tượng datetime"""
        try:
            time_part = log_str.split(": ")[0]
            return datetime.strptime(f"{year}/{time_part}", "%Y/%d/%m %H:%M")
        except:
            return None

    @staticmethod
    def get_days_diff(t_start, t_end):
        """Tính số ngày chênh lệch giữa 2 mốc thời gian"""
        if t_start and t_end:
            return (t_end - t_start).days
        return 0

def is_folder_really_empty(folder_path):
    """Kiểm tra folder có thực sự trống (loại bỏ file ẩn hệ thống)"""
    if not os.path.exists(folder_path): return True
    files = [f for f in os.listdir(folder_path) if f not in ['.DS_Store', 'Thumbs.db', 'desktop.ini']]
    return len(files) == 0