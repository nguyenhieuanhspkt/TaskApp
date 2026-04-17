import os
import numpy as np
import re
import pickle
from sentence_transformers import SentenceTransformer, CrossEncoder
from whoosh.index import open_dir, exists_in, create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path='keepitreal/vietnamese-sbert', index_dir="vattu_index"):
        self.index_dir = index_dir
        
        # TẦNG 3: Bi-Encoder (Nghĩa tổng quát)
        # Dùng model 'keepitreal/vietnamese-sbert' để tránh lỗi OSError
        self.bi_model = SentenceTransformer(model_path)
        
        # TẦNG 2: Cross-Encoder (Thầy chấm thi - So nghĩa trực tiếp)
        # Model này cực kỳ thông minh trong việc phân biệt HCl và NaOH
        self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Schema cho Whoosh (Tầng 1)
        self.schema = Schema(
            ma_vattu=ID(stored=True),
            ten_vattu=TEXT(stored=True),
            thong_so=TEXT(stored=True),
            all_text=TEXT(stored=True)
        )

    def search(self, query_str, top_k=15):
        if not exists_in(self.index_dir): return []
        ix = open_dir(self.index_dir)
        
        # --- BƯỚC 1: LÀM SẠCH QUERY (Quan trọng nhất) ---
        # Loại bỏ các ký tự đặc biệt dễ làm Whoosh hiểu lầm là lệnh logic
        clean_query = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]', ' ', query_str)
        # Loại bỏ các từ thừa chỉ có 1 ký tự (trừ số)
        query_words = [w for w in clean_query.split() if len(w) > 1 or w.isdigit()]
        final_query_str = " ".join(query_words)

        candidates = []
        with ix.searcher() as searcher:
            # Dùng OrGroup(0.5): Chỉ cần khớp 50% số từ là bốc ra luôn, không cần khớp hết
            og = OrGroup.factory(0.5) 
            parser = MultifieldParser(["ten_vattu", "thong_so"], ix.schema, group=og)
            
            query = parser.parse(final_query_str)
            results = searcher.search(query, limit=100) 
            
            for hit in results:
                candidates.append({
                    "ma": hit['ma_vattu'],
                    "ten": hit['ten_vattu'],
                    "ts": hit['thong_so'],
                    "all_text": hit['all_text'],
                    "w_score": hit.score
                })
        
        if not candidates:
            return []

        # --- BƯỚC 2: CROSS-ENCODER SOI NGHĨA (Đã tải xong model nên sẽ rất nhanh) ---
        top_candidates = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_candidates]
        cross_scores = self.cross_model.predict(pairs)

        # --- BƯỚC 3: BI-ENCODER & BONUS ---
        query_vec = self.bi_model.encode(query_str)
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_candidates):
            s_cross = float(cross_scores[i])
            doc_vec = self.bi_model.encode(c['all_text'])
            s_bi = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-9)
            
            # Thưởng điểm cho các số model (185, 315, 3000)
            bonus = 0
            for num in query_numbers:
                if len(num) >= 2 and num in c['all_text']:
                    bonus += 3.0 

            # Phạt nếu nhầm nhóm vật tư
            penalty = 0
            if "hcl" in query_str.lower() and "naoh" in c['all_text'].lower(): penalty = 10
            if "sealant" in query_str.lower() and "van" in c['all_text'].lower(): penalty = 5

            # Tổng điểm cân bằng 70/30
            c['ai_relevance'] = s_cross
            c['final_score'] = (s_cross * 0.7) + (s_bi * 2.0) + (c['w_score'] * 0.1) + bonus - penalty

        top_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        return top_candidates[:top_k]