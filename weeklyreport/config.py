# config.py
import os

# Đường dẫn đến thư mục chứa file tasks.json
JSON_ROOT = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\TaskApp"

# Đường dẫn đầy đủ đến file json
JSON_FILE_PATH = os.path.join(JSON_ROOT, "tasks.json")

# Tên file Excel đầu ra
OUTPUT_FILENAME = "reportTuan.xlsx"

# Danh mục để nhận diện Pháp chế/Thanh tra
SPECIAL_CATEGORY = "Khác"