import os
import json  # <-- THÊM DÒNG NÀY VÀO ĐÂY
import pandas as pd
from google import genai
from pathlib import Path
from dotenv import load_dotenv
from pathlib import Path
class MaterialProcessor:
    @staticmethod
    def _load_api_key():
        """Hard code API Key trực tiếp"""
        return "AIzaSyBkaYzBTjwVKd3rl4p3VM7ZhAiGVsP7SrQ" # Dán cái Key của bạn vào giữa dấu ngoặc kép này

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
        print("\n" + "="*50)
        print("🚀 [NEW SDK] KHỞI CHẠY KIỂM TRA TRÙNG LẶP AI")
        print("="*50)

        # 1. Chạy Pandas & Reset Index
        working_df = MaterialProcessor.mark_duplicates(df, col_name, col_spec)
        working_df = working_df.reset_index(drop=True)
        print(f"✅ Bước 1: Đã chạy Pandas. Tổng số dòng: {len(working_df)}")

        # 2. Lấy API Key
        api_key = MaterialProcessor._load_api_key()
        if not api_key:
            print("❌ LỖI: Không tìm thấy API Key.")
            return working_df

        # 3. Khởi tạo Client theo chuẩn thư viện 'google-genai' mới
        try:
            client = genai.Client(api_key=api_key)
            print("✅ Bước 2: Đã khởi tạo Google GenAI Client.")
        except Exception as e:
            print(f"❌ LỖI khởi tạo Client: {e}")
            return working_df

        # 4. Chuẩn bị dữ liệu cho AI
        data_list = working_df[[col_name, col_spec]].head(50).to_dict(orient='records')
        
        prompt = f"""
        Bạn là chuyên gia thẩm định vật tư cơ khí tại nhà máy.
        Tìm các dòng vật tư tương đương (cùng loại nhưng viết khác nhau).
        Dữ liệu: {data_list}
        Trả về JSON list các nhóm index trùng. Ví dụ: [[0, 2], [5, 10]]
        Chỉ trả về JSON, không giải thích.
        """

        # 5. Gọi AI xử lý
        try:
            print(f"📡 Đang gửi dữ liệu sang Gemini 3 Flash...")
            
            response = client.models.generate_content(
                # Thử lần lượt các tên này nếu vẫn bị 404:
                # 1. 'gemini-3-flash' 
                # 2. 'models/gemini-3-flash'
                model='gemini-3-flash', 
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )
            
            res_text = response.text.strip()
            print(f"📩 AI phản hồi: {res_text}")
            
            duplicate_groups = json.loads(res_text)

            if not duplicate_groups:
                print("ℹ️ AI không tìm thấy thêm nhóm trùng.")
                return working_df

            # 6. Cập nhật kết quả vào DataFrame
            current_max_id = working_df['Group_ID'].max() if pd.notna(working_df['Group_ID'].max()) else 0
            
            for group in duplicate_groups:
                if len(group) < 2: continue
                current_max_id += 1
                for idx in group:
                    if idx < len(working_df):
                        working_df.at[idx, 'Group_ID'] = current_max_id
                        working_df.at[idx, 'Is_Duplicate'] = True
            
            print(f"🎯 Đã cập nhật xong {len(duplicate_groups)} nhóm từ AI.")

        except Exception as e:
            print(f"⚠️ Lỗi thực thi AI: {e}")

        print("="*50 + "\n")
        return working_df