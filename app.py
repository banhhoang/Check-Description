import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & MASTER RULES
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

MASTER_RULES = {
    "BOLT": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
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

def get_api_data(mpn, token, prefix):
    """
    HÀM GỌI API: Trả về chuỗi mô tả chuẩn (VD: 'CAP-CER;10uF,10%,0402,16V,C0G,Auto')
    """
    if not token: return None
    # --- CHÈN CÂU LỆNH GRAPHQL CỦA BẠN VÀO ĐÂY ---
    # response = requests.post(URL, headers={"Authorization": f"Bearer {token}"}, json={"query": "..."})
    # data = response.json()
    # return f"{prefix};GIÁ_TRỊ_TỪ_API"
    
    return f"{prefix};10uF,10%,0402,16V,C0G,Auto" # Dữ liệu demo (Thay thế bằng code thật)

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
    return master_name[:37] + "...", "Cảnh báo: Vẫn > 40"

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="Check Description", layout="wide")
st.title("🛠️ Check Description")

token = get_nexar_token()
st.sidebar.metric("API Nexar", "Connected" if token else "Disconnected")

uploaded_file = st.file_uploader("📂 Upload BOM (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra"):
        with st.spinner("Đang xử lý..."):
            results = []
            for _, row in df.iterrows():
                desc = str(row['Mô tả/Yêu cầu kỹ thuật']).strip()
                mpn = str(row['Mã NSX'])
                
                prefix = desc.split(";")[0]
                rule = MASTER_RULES.get(prefix)
                
                # --- XỬ LÝ DỮ LIỆU ---
                if rule and rule["type"] == "electronic" and token:
                    # Lấy mô tả chuẩn từ API
                    master_name = get_api_data(mpn, token, prefix)
                    # Tạo suggest từ API data
                    values = master_name.split(";")[1].split(",")
                    suggested, note = get_truncation(prefix, rule, values)
                    status = "🟢 PASS"
                elif rule:
                    # Nhóm cơ khí hoặc không có API
                    master_name = desc
                    values = desc.split(";")[1].split(",")
                    suggested, note = get_truncation(prefix, rule, values)
                    status = "🟢 PASS" if rule["type"] == "mechanical" else "🔴 FAIL (API)"
                else:
                    master_name, suggested, note, status = "-", "-", "Thiếu quy tắc", "🟡 WARNING"
                
                results.append({"Status": status, "Master Name": master_name, "Suggest": suggested, "Note": note})

            res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
            st.dataframe(res_df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("📥 Tải báo cáo", output.getvalue(), "Report.xlsx")
