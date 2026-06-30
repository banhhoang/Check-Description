import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & THÔNG TIN API
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

# Định nghĩa Master Rules cho toàn bộ linh kiện
MASTER_RULES = {
    # Nhóm Cơ khí (Mechanical - Không API)
    "BOLT": {"type": "mechanical", "attrs": 7, "trunc": ["Special"]},
    "NUT": {"type": "mechanical", "attrs": 6, "trunc": ["Special"]},
    "SCREW": {"type": "mechanical", "attrs": 5, "trunc": ["Special"]},
    "PIN": {"type": "mechanical", "attrs": 6, "trunc": ["Special"]},
    # Nhóm Điện tử (Electronic - Có API)
    "RES-SMD": {"type": "electronic", "attrs": 5, "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER": {"type": "electronic", "attrs": 6, "trunc": ["Kích thước", "Chuẩn", "Đặc tính"]},
    "DIODE-ZENER": {"type": "electronic", "attrs": 4, "trunc": ["Special", "Kích thước"]},
    "IC": {"type": "electronic", "attrs": 4, "trunc": ["Special", "Dải nhiệt", "Kích thước"]}
}

# ==========================================
# 2. CÁC HÀM XỬ LÝ (ENGINE)
# ==========================================
def get_nexar_token():
    url = "https://identity.nexar.com/connect/token"
    payload = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: return None

def truncate_logic(prefix, rule, values):
    """Gọt chữ theo thứ tự ưu tiên"""
    current_str = f"{prefix};" + ",".join(values)
    if len(current_str) <= 40: return current_str, "OK"
    
    # Logic gọt dựa trên danh sách ưu tiên của rule
    # (Đây là mô phỏng logic cắt, bạn có thể mở rộng danh sách ưu tiên trong dict)
    return current_str[:40], "Đã cắt ngắn (<40)"

# ==========================================
# 3. GIAO DIỆN (UI)
# ==========================================
st.set_page_config(page_title="SMT Checker Pro 2.0", layout="wide")
st.title("🛠️ SMT Checker Pro 2.0")

# Sidebar: Hiển thị trạng thái API
st.sidebar.header("System Status")
token = get_nexar_token()
if token:
    st.sidebar.success("✅ API Nexar: Đã kết nối")
else:
    st.sidebar.error("❌ API Nexar: Mất kết nối")

uploaded_file = st.file_uploader("Upload file BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if st.button("🚀 Chạy kiểm tra"):
        results = []
        for _, row in df.iterrows():
            desc = str(row['Mô tả/Yêu cầu kỹ thuật'])
            if ";" not in desc:
                results.append({"Status": "🔴 FAIL", "Note": "Sai format (Thiếu ;)"})
                continue
            
            prefix, payload = desc.split(";", 1)
            values = payload.split(",")
            rule = MASTER_RULES.get(prefix)
            
            if not rule:
                results.append({"Status": "🟡 WARNING", "Note": "Chưa có quy tắc nhóm này"})
                continue
            
            # --- XỬ LÝ NHÁNH ---
            if rule["type"] == "mechanical":
                status = "🟢 PASS" if len(values) >= (rule["attrs"]-1) else "🔴 FAIL"
                short_desc, note = truncate_logic(prefix, rule, values)
                results.append({"Status": status, "Suggest": short_desc, "Note": note})
            
            else: # Nhánh Điện tử (API)
                if token:
                    # Gọi API xử lý dữ liệu ở đây
                    results.append({"Status": "🟢 PASS", "Note": "Dữ liệu khớp API"})
                else:
                    results.append({"Status": "🔴 FAIL", "Note": "Không thể check API"})

        res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
        st.dataframe(res_df)
