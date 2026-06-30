import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & QUY TẮC (MASTER RULES)
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

# Định nghĩa quy tắc chi tiết
MASTER_RULES = {
    "BOLT": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "NUT": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "SCREW": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Special"], "trunc": ["Special"]},
    "RES-SMD": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "Đặc tính"]},
    "DIODE": {"type": "electronic", "attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "IC": {"type": "electronic", "attrs": ["Chức năng", "Dải nhiệt", "Kích thước", "Special"], "trunc": ["Special", "Dải nhiệt", "Kích thước"]}
}

# ==========================================
# 2. CÁC HÀM XỬ LÝ (CORE)
# ==========================================
def get_nexar_token():
    url = "https://identity.nexar.com/connect/token"
    payload = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    try:
        r = requests.post(url, data=payload, timeout=5)
        return r.json().get("access_token")
    except: return None

def get_truncation(prefix, rule, values):
    master_name = f"{prefix};" + ",".join(values)
    if len(master_name) <= 40: return master_name, "OK"
    
    data = dict(zip(rule["attrs"], values))
    history = []
    for target in rule["trunc"]:
        if target in data:
            data.pop(target)
            history.append(target)
            new_str = f"{prefix};" + ",".join([str(v) for v in data.values() if v])
            if len(new_str) <= 40: return new_str, f"Gọt: {','.join(history)}"
    return master_name[:37] + "...", "Cảnh báo: Vẫn > 40 ký tự"

# ==========================================
# 3. GIAO DIỆN (UI)
# ==========================================
st.set_page_config(page_title="Check Description", layout="wide")
st.title("🛠️ Check Description")
st.markdown("---")

# Sidebar
st.sidebar.header("System Status")
token = get_nexar_token()
st.sidebar.metric("API Nexar", "Connected" if token else "Disconnected", delta=None)

# Main Area
uploaded_file = st.file_uploader("📂 Upload file BOM (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra"):
        with st.spinner("Đang xử lý dữ liệu..."):
            results = []
            for _, row in df.iterrows():
                desc = str(row['Mô tả/Yêu cầu kỹ thuật']).strip()
                
                if ";" not in desc:
                    results.append({"Status": "🔴 FAIL", "Master Name": "-", "Suggest": "-", "Note": "Sai format"})
                    continue
                
                prefix, payload = desc.split(";", 1)
                values = [v.strip() for v in payload.split(",")]
                rule = MASTER_RULES.get(prefix)
                
                if not rule:
                    results.append({"Status": "🟡 WARNING", "Master Name": "-", "Suggest": "-", "Note": "Chưa có quy tắc"})
                    continue
                
                master_name = f"{prefix};{payload}"
                suggested, note = get_truncation(prefix, rule, values)
                
                # Logic phân nhánh
                if rule["type"] == "mechanical":
                    status = "🟢 PASS" if len(values) >= (len(rule["attrs"])-1) else "🔴 FAIL"
                else:
                    status = "🟢 PASS" if token else "🔴 FAIL (Thiếu API)"
                    
                results.append({"Status": status, "Master Name": master_name, "Suggest": suggested, "Note": note})

            # Hiển thị kết quả
            res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
            st.success("Kiểm tra hoàn tất!")
            st.dataframe(res_df, use_container_width=True)
            
            # Xuất file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res_df.to_excel(writer, index=False)
            
            st.download_button("📥 Tải file báo cáo (.xlsx)", data=output.getvalue(), file_name="BOM_Check_Result.xlsx")
