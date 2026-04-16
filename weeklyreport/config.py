# config.py
import os

# Đường dẫn JSON
JSON_ROOT = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\TaskApp"
JSON_FILE_PATH = os.path.join(JSON_ROOT, "tasks.json")

# Tên file xuất
OUTPUT_FILENAME = "reportTuan.xlsx"

# CHUẨN HÓA NGÀY THÁNG
# Định dạng bạn muốn hiển thị trong file Excel (Ví dụ: 16/04/2026)
DATE_FORMAT_OUT = "%d/%m/%Y"

# Danh mục ưu tiên
SPECIAL_CATEGORY = "Khác"