import pandas as pd
from AIgemini import MaterialProcessor

def test_material_grouping():
    # 1. Tạo dữ liệu giả lập (Mock Data)
    # Bao gồm các trường hợp thực tế tại nhà máy:
    # - Dòng 0 & 1: Trùng hoàn toàn
    # - Dòng 2: Trùng tên nhưng khác thông số (Không được coi là trùng)
    # - Dòng 3 & 4: Trùng nhưng viết hoa/thường và khoảng trắng lung tung
    data = {
        'Tên vật tư': [
            'Van cửa thép', 
            'Van cửa thép', 
            'Van cửa thép', 
            'Lọc dầu thủy lực', 
            '  LOC dau thuy LUC  '
        ],
        'Thông số': [
            'DN150 PN16', 
            'DN150 PN16', 
            'DN200 PN25', 
            'Model: ABC-123', 
            'model: abc-123'
        ],
        'Mã giá': ['G01', 'G01', 'G02', 'G03', 'G04']
    }
    
    df = pd.DataFrame(data)
    
    print("--- DỮ LIỆU ĐẦU VÀO GIẢ LẬP ---")
    print(df)
    print("\n" + "="*50 + "\n")

    # 2. Chạy hàm xử lý từ class MaterialProcessor
    print("Đang thực hiện phân nhóm vật tư...")
    processed_df = MaterialProcessor.mark_duplicates(
        df, 
        col_name='Tên vật tư', 
        col_spec='Thông số'
    )

    # 3. Hiển thị kết quả
    print("--- KẾT QUẢ SAU KHI XỬ LÝ ---")
    # Hiển thị các cột quan trọng để kiểm tra
    cols_to_show = ['Tên vật tư', 'Thông số', 'Is_Duplicate', 'Group_ID']
    print(processed_df[cols_to_show])

    # 4. Kiểm chứng logic
    print("\n--- PHÂN TÍCH LOGIC ---")
    group_1 = processed_df[processed_df['Group_ID'] == 1]
    if len(group_1) == 2:
        print("✅ Thành công: Đã nhận diện đúng cặp 'Van cửa thép' trùng nhau.")
    
    group_2 = processed_df[processed_df['Group_ID'] == 2]
    if len(group_2) == 2:
        print("✅ Thành công: Đã nhận diện đúng 'Lọc dầu' trùng nhau bất kể viết hoa/khoảng trắng.")

if __name__ == "__main__":
    test_material_grouping()