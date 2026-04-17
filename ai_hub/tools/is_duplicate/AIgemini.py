import os
import json  # <-- THÊM DÒNG NÀY VÀO ĐÂY
import pandas as pd
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

class MaterialProcessor:
    @staticmethod
    def _load_api_key():
        """Hàm nội bộ để nạp API Key từ thư mục gốc TaskApp"""
        try:
            # Nhảy ngược 4 cấp: is_duplicate -> tools -> ai_hub -> TaskApp
            root_path = Path(__file__).resolve().parents[3]
            env_path = root_path / '.env'
            load_dotenv(dotenv_path=env_path)
            return os.getenv("API-KEY-GOOGLE")
        except:
            return None

    @staticmethod
    def mark_duplicates(df, col_name='Tên vật tư', col_spec='Thông số kỹ thuật'):
        """Thuật toán Pandas cũ của anh để xử lý thô nhanh chóng"""
        if df is None or df.empty: return df
        working_df = df.copy()
        
        if col_name not in working_df.columns or col_spec not in working_df.columns:
            return working_df

        norm_name = working_df[col_name].astype(str).str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
        norm_spec = working_df[col_spec].astype(str).str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
        match_key = norm_name + "##" + norm_spec

        working_df['Is_Duplicate'] = match_key.duplicated(keep=False)
        working_df['Group_ID'] = None
        
        duplicate_keys = match_key[working_df['Is_Duplicate']].unique()
        key_to_id = {key: i + 1 for i, key in enumerate(duplicate_keys)}
        
        mask = match_key.isin(duplicate_keys)
        working_df.loc[mask, 'Group_ID'] = match_key.map(key_to_id)
        return working_df

    @staticmethod
    def mark_duplicates_with_ai(df, col_name='Tên vật tư', col_spec='Thông số kỹ thuật'):
        # 1. Chạy thuật toán Pandas trước để có Group_ID cơ bản
        working_df = MaterialProcessor.mark_duplicates(df, col_name, col_spec)
        
        # 2. Lấy API Key và cấu hình
        api_key = MaterialProcessor._load_api_key()
        if not api_key: return working_df
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 3. Chuẩn bị dữ liệu cho AI (Gửi danh sách để AI tìm các cặp tương đương)
        # Chỉ gửi các dòng chưa bị Code thường bắt được hoặc toàn bộ để AI rà soát lại
        data_list = working_df[[col_name, col_spec]].head(50).to_dict(orient='records')
        
        prompt = f"""
        Bạn là chuyên gia thẩm định vật tư cơ khí điện tại nhà máy.
        Nhiệm vụ: Tìm các dòng vật tư tương đương nhau trong danh sách dưới đây.
        
        Danh sách: {data_list}
        
        YÊU CẦU QUAN TRỌNG:
        - Trả về kết quả duy nhất dưới dạng JSON list của các list chỉ số dòng (index) trùng nhau.
        - Ví dụ: [[0, 2, 5], [1, 4]] nghĩa là dòng 0, 2, 5 là một loại; dòng 1, 4 là một loại.
        - Chỉ trả về mã JSON, không giải thích gì thêm.
        """

        try:
            response = model.generate_content(prompt)
            # Làm sạch chuỗi JSON từ AI (loại bỏ ```json ... ``` nếu có)
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            duplicate_groups = json.loads(clean_json)

            # 4. Cập nhật Group_ID mới từ AI vào DataFrame
            # Bắt đầu Group_ID của AI sau Group_ID lớn nhất của Pandas để không bị trùng
            current_max_id = working_df['Group_ID'].max() if pd.notna(working_df['Group_ID'].max()) else 0
            
            for group in duplicate_groups:
                current_max_id += 1
                for idx in group:
                    if idx < len(working_df):
                        working_df.at[idx, 'Group_ID'] = current_max_id
                        working_df.at[idx, 'Is_Duplicate'] = True

        except Exception as e:
            print(f"Lỗi xử lý logic AI: {e}")

        return working_df