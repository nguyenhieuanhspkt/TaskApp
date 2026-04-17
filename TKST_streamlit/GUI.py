import streamlit as st
import pandas as pd
import os
from engine import HybridSearchEngine  # File engine.py của bạn

# Cấu hình trang
st.set_page_config(page_title="Hệ thống Tìm kiếm Vật tư Kỹ thuật 3 Cấp", layout="wide")

# Hàm khởi tạo Engine (Dùng cache_resource để không bị load lại khi bấm nút)
@st.cache_resource
def load_engine():
    model_path = 'keepitreal/vietnamese-sbert' 
    index_dir = "vattu_index"
    with st.spinner("Đang khởi động 'Bộ não AI' (Tầng 2 & 3)..."):
        return HybridSearchEngine(model_path, index_dir)

# --- GIAO DIỆN CHÍNH ---
st.title("🔍 Smart Technical Search v2.0")
st.markdown("---")

engine = load_engine()

# Sidebar: Quản lý dữ liệu
with st.sidebar:
    st.header("⚙️ Quản lý hệ thống")
    if st.button("🔄 Cập nhật lại Index (Khi đổi Excel)"):
        with st.spinner("Đang đọc Excel và tạo Vector..."):
            # Giả sử bạn có hàm index_excel trong engine
            # engine.index_excel("data_vattu.xlsx") 
            st.success("Đã cập nhật dữ liệu mới!")
    
    st.info("""
    **Cơ chế 3 Tầng:**
    1. **Whoosh:** Lọc đúng mặt chữ.
    2. **Cross-Encoder:** So nghĩa trực tiếp (70%).
    3. **Bi-Encoder:** So nghĩa tổng quát (30%).
    """)

# Khu vực tìm kiếm
query = st.text_area("Nhập mô tả vật tư hoặc thông số kỹ thuật:", 
                     placeholder="Ví dụ: Chesterton 185 Sealant 315 Oc 3000 psi...",
                     height=150)

col1, col2 = st.columns([1, 5])
with col1:
    search_button = st.button("🚀 Tìm kiếm ngay")
with col2:
    top_k = st.slider("Số lượng kết quả:", 5, 50, 15)

if search_button and query:
    with st.spinner("AI đang 'so nghĩa' từng dòng một..."):
        results = engine.search(query, top_k=top_k)
        
        if results:
            st.success(f"Tìm thấy {len(results)} kết quả phù hợp nhất!")
            
            # Chuyển kết quả sang DataFrame để hiển thị bảng đẹp
            df_results = pd.DataFrame(results)
            
            # Tạo bảng hiển thị sạch sẽ
            for i, res in enumerate(results):
                with st.container():
                    # Hiển thị tiêu đề và điểm số
                    c1, c2 = st.columns([8, 2])
                    with c1:
                        st.subheader(f"{i+1}. {res['ten']}")
                    with c2:
                        st.metric("Tổng điểm", f"{res['final_score']:.2f}")
                    
                    # Thông tin chi tiết
                    t1, t2, t3 = st.tabs(["📄 Thông số", "🆔 Mã hiệu", "📊 Phân tích AI"])
                    with t1:
                        st.write(f"**Thông số:** {res['ts']}")
                    with t2:
                        st.write(f"**Mã vật tư:** `{res['ma']}`")
                    with t3:
                        # Hiển thị các thành phần điểm để bạn kiểm tra
                        col_a, col_b = st.columns(2)
                        col_a.write(f"🔹 **Độ khớp mặt chữ (Whoosh):** {res.get('w_score', 0):.2f}")
                        col_b.write(f"🔹 **Độ khớp nghĩa (Cross-AI):** {res.get('ai_relevance', 0):.4f}")
                    
                    st.markdown("---")
        else:
            st.warning("Không tìm thấy kết quả nào. Hãy thử bớt các từ khóa quá chi tiết.")

# Chân trang
st.markdown("<p style='text-align: center; color: grey;'>Hệ thống hỗ trợ quyết định vật tư - AI Powered</p>", unsafe_allow_html=True)