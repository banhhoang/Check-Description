import streamlit as st
import pandas as pd
import requests
import re
import io

# ==========================================
# 1. CẤU HÌNH API NEXAR
# ==========================================
NEXAR_CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
NEXAR_CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

def get_nexar_token():
    """Lấy Access Token từ Nexar bằng OAuth2"""
    url = "https://identity.nexar.com/connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": NEXAR_CLIENT_ID,
        "client_secret": NEXAR_CLIENT_SECRET
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        return None

# ==========================================
# 2. BỘ NÃO XỬ LÝ QUY TẮC (MASTER RULES ENGINE)
# ==========================================
def normalize_column_name(cols, target_keywords):
    """Tìm tên cột linh hoạt (không phân biệt hoa/thường, khoảng trắng)"""
    for col in cols:
        col_lower = str(col).lower().replace(" ", "")
        for kw in target_keywords:
            if kw.replace(" ", "").lower() in col_lower:
                return col
    return None

def check_res_smd(description):
    """Kiểm tra định dạng nhóm Điện trở dán (RES-SMD)"""
    bom_desc = str(description).strip()
    cleaned_desc = re.sub(r'\s+', '', bom_desc) # Xóa khoảng trắng để check
    
    errors = []
    if ";" not in bom_desc:
        errors.append("Thiếu dấu chấm phẩy (;)")
    if "," not in bom_desc:
        errors.append("Thiếu dấu phẩy (,) ngăn cách")
    if not cleaned_desc.startswith("RES-SMD;"):
        errors.append("Sai tiền tố. Cần bắt đầu bằng 'RES-SMD;'")
    if "KOHM" not in cleaned_desc.upper() and "OHM" in cleaned_desc.upper():
        errors.append("Giá trị chưa chuẩn hóa (Cần viết liền OHM, KOHM, MOHM)")
        
    status = "🟢 PASS" if not errors else "🔴 FAIL"
    return status, " | ".join(errors) if errors else "Đúng chuẩn định dạng"

# ==========================================
# 3. LUỒNG XỬ LÝ FILE BOM
# ==========================================
def process_bom(df, token):
    # Tìm linh hoạt tên cột Mô tả và Mã NSX
    desc_col = normalize_column_name(df.columns, ["môtả", "mota", "yêucầukỹthuật"])
    mpn_col = normalize_column_name(df.columns, ["mãnsx", "mansx", "partnumber"])
    
    if not desc_col or not mpn_col:
        st.error("❌ Không tìm thấy cột 'Mô tả' hoặc 'Mã NSX' trong file Excel!")
        return None

    status_list = []
    error_list = []
    
    # Quét qua từng dòng
    for index, row in df.iterrows():
        desc_val = str(row[desc_col])
        part_number = str(row[mpn_col])
        
        # Phân loại luồng xử lý theo tiền tố kỹ sư nhập
        if "RES" in desc_val.upper() or "TRỞ" in desc_val.upper():
            status, err_msg = check_res_smd(desc_val)
        else:
            # Tạm bỏ qua các nhóm khác hoặc áp dụng luật chung
            status, err_msg = ("🟡 WARNING", "Chưa có quy tắc check cho nhóm này")
            
        status_list.append(status)
        error_list.append(err_msg)

    # Ghi nhận kết quả vào DataFrame
    df['Trạng thái Format'] = status_list
    df['Chi tiết lỗi (PL01/PL02)'] = error_list
    
    # Xử lý định dạng dấu chấm thập phân cho giá (nếu có cột giá)
    price_col = normalize_column_name(df.columns, ["1000pcsprice", "giá"])
    if price_col:
        df[price_col] = df[price_col].astype(str).str.replace(',', '.')

    return df

# ==========================================
# 4. GIAO DIỆN STREAMLIT (UI)
# ==========================================
st.set_page_config(page_title="SMT Checker Pro", layout="wide")
st.title("🛠️ SMT Checker Pro - Validation Engine")
st.markdown("Hệ thống kiểm tra BOM đối chiếu chuẩn **PL01/PL02** và API Nexar.")

st.sidebar.header("Trạng thái API")
token = get_nexar_token()
if token:
    st.sidebar.success("✅ Đã kết nối Nexar API")
else:
    st.sidebar.error("❌ Mất kết nối API (Kiểm tra lại Client ID/Secret)")

uploaded_file = st.file_uploader("Kéo thả file BOM Excel vào đây", type=["xlsx", "xls"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    st.write("### Dữ liệu đầu vào", df_input.head(3))
    
    if st.button("🚀 Chạy đối chiếu BOM", type="primary"):
        with st.spinner("Đang phân tích cấu trúc và truy vấn dữ liệu..."):
            df_result = process_bom(df_input.copy(), token)
            
        if df_result is not None:
            st.success("Hoàn tất kiểm tra!")
            st.dataframe(df_result, use_container_width=True)
            
            # Xuất file Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Report')
            output.seek(0)
            
            st.download_button(
                label="📥 Tải xuống File Báo Cáo (.xlsx)",
                data=output,
                file_name="BOM_Validation_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
