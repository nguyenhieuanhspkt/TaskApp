import os
import numpy as np
import re
from sentence_transformers import SentenceTransformer, CrossEncoder
from whoosh.index import open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path='keepitreal/vietnamese-sbert', index_dir="vattu_index"):
        self.index_dir = index_dir
        
        # TẦNG 3: Bi-Encoder (Nghĩa tổng quát)
        self.bi_model = SentenceTransformer(model_path)
        
        # TẦNG 2: Cross-Encoder (So nghĩa trực tiếp - Reranker)
        self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def clean_text(self, text):
        """Làm sạch query: bỏ ký tự đặc biệt để Whoosh không bị lỗi"""
        if not text: return ""
        # Thay thế các ký tự đặc biệt bằng khoảng trắng
        text = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]', ' ', text)
        # Loại bỏ các từ 1 ký tự đứng lẻ loi (trừ số)
        words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
        return " ".join(words)

    def search(self, query_str, top_k=15):
        if not exists_in(self.index_dir):
            return []
        
        ix = open_dir(self.index_dir)
        
        # 1. LÀM SẠCH VÀ CHUẨN BỊ QUERY
        clean_query = self.clean_text(query_str)
        if not clean_query: clean_query = query_str # Fallback nếu xóa hết
        
        # --- BƯỚC 1: WHOOSH LỌC NHANH (TẦNG 1) ---
        candidates = []
        with ix.searcher() as searcher:
            # OrGroup(0.5): Chỉ cần khớp 50% từ khóa là lấy, tránh việc quá khắt khe
            og = OrGroup.factory(0.5)
            parser = MultifieldParser(["ten_vattu", "thong_so"], ix.schema, group=og)
            query = parser.parse(clean_query)
            
            # Lấy 100 ứng viên tiềm năng nhất
            results = searcher.search(query, limit=100)
            
            for hit in results:
                # NẠP THÊM ĐOẠN CODE CỦA BẠN VÀO ĐÂY
                candidates.append({
                    "ma": hit['ma_vattu'],
                    "erp": hit['ma_erp'], # Bốc mã ERP ra đây
                    "ten": hit['ten_vattu'],
                    "ts": hit['thong_so'],
                    "all_text": hit['all_text'],
                    "w_score": hit.score
                })
        
        if not candidates:
            return []

        # --- BƯỚC 2: CROSS-ENCODER (TẦNG 2 - SO NGHĨA TRỰC TIẾP) ---
        # Lấy Top 30 ông từ Whoosh để "giám định" kỹ
        top_candidates = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_candidates]
        
        # Model này sẽ chấm điểm dựa trên sự tương tác thực tế giữa câu hỏi và kết quả
        cross_scores = self.cross_model.predict(pairs)

        # --- BƯỚC 3: BI-ENCODER & CHỐT CHẶN KỸ THUẬT (TẦNG 3) ---
        query_vec = self.bi_model.encode(query_str)
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_candidates):
            # Điểm từ tầng 2 (Nghĩa trực tiếp)
            s_cross = float(cross_scores[i])
            
            # Điểm từ tầng 3 (Nghĩa tổng quát)
            doc_vec = self.bi_model.encode(c['all_text'])
            s_bi = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-9)
            
            # THƯỞNG ĐIỂM CON SỐ (Mã hiệu, Size, Nhiệt độ)
            bonus = 0
            text_lower = c['all_text'].lower()
            for num in query_numbers:
                if len(num) >= 2 and num in text_lower:
                    bonus += 2.0 # Thưởng cho mỗi con số khớp

            # HÌNH PHẠT XUNG ĐỘT (Để trị lỗi HCl vs NaOH)
            penalty = 0
            q_low = query_str.lower()
            if "hcl" in q_low and "naoh" in text_lower: penalty = 15.0
            if "sealant" in q_low and "van" in text_lower: penalty = 8.0

            # CÔNG THỨC TỔNG HỢP: 70% Nghĩa trực tiếp + 20% Nghĩa rộng + 10% Chữ cái
            c['ai_relevance'] = s_cross
            c['final_score'] = (s_cross * 1.5) + (s_bi * 3.0) + (c['w_score'] * 0.1) + bonus - penalty

        # Sắp xếp lại theo điểm cuối cùng
        top_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        return top_candidates[:top_k]