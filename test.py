import pandas as pd

# Đường dẫn file Excel
file_path = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\Thẩm định 121_hieuna_3\2026-04-09-Gửi lần 2- HSMT GT 42\hsmt gửi TTĐ.xlsx"

# Đọc sheet tên là 'TTD'
df = pd.read_excel(
    file_path,
    sheet_name="TTD",
    engine="openpyxl"
)

# Xem 5 dòng đầu
print(df.head())

# Xem thông tin tổng quát
print(df.info())