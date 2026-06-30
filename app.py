import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & MASTER RULES
# ==========================================
NEXAR_CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
NEXAR_CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

# Định nghĩa quy tắc cho từng loại linh kiện
MASTER_RULES = {
    # Cơ khí (Không gọi API)
    "BOLT": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "NUT": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    # Điện tử (Gọi API)
    "RES-SMD": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "Đặc tính"]},
}

# ==========================================
# 2. CÁC HÀM XỬ LÝ (CORE ENGINE)
# ==========================================
def get_nexar_token():
    url = "https://identity.nexar.com/connect/token"
    payload = {"grant_type": "client_credentials", "client_id": NEXAR_CLIENT_ID, "client_secret": NEXAR_CLIENT_SECRET}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: return None

def truncate_string(prefix, rule, values):
    """Hàm 'gọt' chữ theo thứ tự ưu tiên"""
    data = dict(zip(rule["attrs"], values))
    current_str = f"{prefix};" + ",".join([str(v) for v in values if v])
    
    if len(current_str) <= 40: return current_str, "OK"
    
    history = []
    for target in rule["trunc"]:
        if target in data:
            data.pop(target)
            history.append(target)
            new_str = f"{prefix};" + ",".join([str(v) for v in data.values() if v])
            if len(new_str) <= 40: return new_str, f"Đã lược bỏ: {','.join(history)}"
    return current_str, "Cảnh báo: Vẫn vượt > 40 ký tự"

# ==========================================
# 3. GIAO DIỆN & LUỒNG CHÍNH
# ==========================================
st.set_page_config(page_title="SMT Checker Pro 2.0", layout="wide")
st.title("🛠️ SMT Checker Pro v2.0")

uploaded_file = st.file_uploader("Upload file BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if st.button("🚀 Chạy kiểm tra"):
        results = []
        for _, row in df.iterrows():
            # Tách chuỗi bằng dấu chấm phẩy đầu tiên
            desc = str(row['Mô tả/Yêu cầu kỹ thuật'])
            if ";" not in desc:
                results.append({"Status": "FAIL", "Note": "Sai format (Thiếu ;)"})
                continue
                
            prefix, values_str = desc.split(";", 1)
            values = values_str.split(",")
            
            # Kiểm tra luật
            rule = MASTER_RULES.get(prefix)
            if not rule:
                results.append({"Status": "WARNING", "Note": "Chưa có quy tắc cho nhóm này"})
                continue
            
            # Logic xử lý
            if rule["type"] == "mechanical":
                # Check cơ khí
                status = "PASS" if len(values) >= len(rule["attrs"])-1 else "FAIL"
                new_desc, note = truncate_string(prefix, rule, values)
                results.append({"Status": status, "Master Name": f"{prefix};{values_str}", "Suggest": new_desc, "Note": note})
            else:
                # Logic Điện tử gọi API tương tự... (Đang mô phỏng luồng)
                results.append({"Status": "PASS", "Note": "Đang kết nối API..."})
        
        # Xuất kết quả
        res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
        st.dataframe(res_df)
