import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH API & MASTER RULES
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

MASTER_RULES = {
    # Nhóm Cơ khí (Không gọi API)
    "BOLT": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "NUT": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "SCREW": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Special"], "trunc": ["Special"]},
    "RES-SMD": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "Đặc tính"]},
    "DIODE": {"type": "electronic", "attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "IC": {"type": "electronic", "attrs": ["Chức năng", "Dải nhiệt", "Kích thước", "Special"], "trunc": ["Special", "Dải nhiệt", "Kích thước"]}
}

# ==========================================
# 2. HÀM XỬ LÝ DỮ LIỆU
# ==========================================
def get_nexar_token():
    url = "https://identity.nexar.com/connect/token"
    payload = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    try:
        r = requests.post(url, data=payload, timeout=5)
        return r.json().get("access_token")
    except: return None

def get_api_description(mpn, token):
    """
    HÀM GỌI API: Bạn điền query GraphQL cụ thể của bạn vào đây
    Hiện tại đang để chế độ mô phỏng để bạn không bị lỗi code.
    """
    if not token or not mpn: return "N/A (Chưa có API)"
    # Gợi ý: Tại đây bạn sẽ thực hiện request.post tới Nexar GraphQL endpoint
    # response = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"query": "..."})
    return f"API_Data_For_{mpn}" # Trả về mô tả lấy từ API

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
# 3. GIAO DIỆN & VÒNG LẶP XỬ LÝ
# ==========================================
st.set_page_config(page_title="Check Description", layout="wide")
st.title("🛠️ Check Description")

token = get_nexar_token()
uploaded_file = st.file_uploader("Upload file BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Kiểm tra"):
        results = []
        for _, row in df.iterrows():
            desc = str(row['Mô tả/Yêu cầu kỹ thuật']).strip()
            mpn = str(row['Mã NSX']) # Lấy MPN để gọi API
            
            # 1. Nhận diện loại linh kiện
            prefix = desc.split(";")[0] if ";" in desc else "UNKNOWN"
            rule = MASTER_RULES.get(prefix)
            
            # 2. Xử lý API (Luôn thực hiện cho Electronic, bất chấp pass hay fail)
            api_desc = "-"
            if rule and rule["type"] == "electronic":
                api_desc = get_api_description(mpn, token)
            
            # 3. Validation Logic
            if not rule:
                results.append({"Status": "🟡 WARNING", "Master Name": "-", "Suggest": "-", "Note": "Chưa có quy tắc"})
            else:
                # Logic check
                is_valid = True if rule["type"] == "mechanical" else (api_desc != "N/A (Chưa có API)")
                status = "🟢 PASS" if is_valid else "🔴 FAIL"
                
                # Cập nhật Master Name
                master_name = api_desc if rule["type"] == "electronic" else desc
                suggested, note = get_truncation(prefix, rule, desc.split(";")[1].split(","))
                
                results.append({"Status": status, "Master Name": master_name, "Suggest": suggested, "Note": note})

        res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
        st.dataframe(res_df)
