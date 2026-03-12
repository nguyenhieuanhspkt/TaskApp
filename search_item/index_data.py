import pandas as pd
import os
import shutil
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID

def create_vattu_index(excel_path, index_dir="vattu_index"):
    # 1. Tạo hoặc làm sạch thư mục index
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.makedirs(index_dir)

    # 2. Định nghĩa cấu trúc dữ liệu cho Whoosh (Đã thêm ma_erp)
    schema = Schema(
        ma_vattu=ID(stored=True),
        ma_erp=ID(stored=True),       # Trường mới để lưu mã ERP
        ten_vattu=TEXT(stored=True),
        thong_so=TEXT(stored=True),
        all_text=TEXT(stored=True)
    )

    # 3. Tạo Index
    ix = create_in(index_dir, schema)
    writer = ix.writer()

    # 4. Đọc dữ liệu từ Excel
    print(f"--- Đang đọc file: {excel_path} ---")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")
        return

    # Đảm bảo không có dòng trống
    df = df.fillna("")

    # 5. Nạp dữ liệu vào Index
    for _, row in df.iterrows():
        # Gộp tất cả bao gồm cả ma_erp vào all_text để tìm kiếm theo từ khóa nào cũng ra
        full_info = f"{row['ten_vattu']} {row['thong_so']} {row['ma_vattu']} {row['ma_erp']}"
        
        writer.add_document(
            ma_vattu=str(row['ma_vattu']),
            ma_erp=str(row['ma_erp']),     # Lưu mã ERP vào trường riêng
            ten_vattu=str(row['ten_vattu']),
            thong_so=str(row['thong_so']),
            all_text=full_info
        )
    
    writer.commit()
    print(f"--- ĐÃ NẠP XONG {len(df)} DÒNG VÀO HỆ THỐNG ---")

if __name__ == "__main__":
    # Đảm bảo file danh_muc_vattu.xlsx có cột 'ma_erp'
    create_vattu_index("danh_muc_vattu.xlsx")