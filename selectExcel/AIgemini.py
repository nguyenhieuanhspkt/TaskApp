import pandas as pd

class MaterialProcessor:
    @staticmethod
    def mark_duplicates(df, col_name='Tên vật tư', col_spec='Thông số'):
        if df is None or df.empty:
            return df
        
        # Luôn làm việc trên một bản sao để tránh lỗi SettingWithCopyWarning
        working_df = df.copy()
        
        if col_name not in working_df.columns or col_spec not in working_df.columns:
            return working_df

        # Chuẩn hóa dữ liệu trong các biến tạm
        norm_name = working_df[col_name].astype(str).str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
        norm_spec = working_df[col_spec].astype(str).str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
        match_key = norm_name + "##" + norm_spec

        # Gán kết quả vào bản sao
        working_df['Is_Duplicate'] = match_key.duplicated(keep=False)
        working_df['Group_ID'] = None
        
        duplicate_keys = match_key[working_df['Is_Duplicate']].unique()
        key_to_id = {key: i + 1 for i, key in enumerate(duplicate_keys)}
        
        # Chỉ gán Group_ID cho những hàng có key nằm trong danh sách trùng
        mask = match_key.isin(duplicate_keys)
        working_df.loc[mask, 'Group_ID'] = match_key.map(key_to_id)

        return working_df