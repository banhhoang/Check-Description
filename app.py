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
    # Nhóm Cơ khí (Không API)
    "BOLT": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "NUT": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Cấp bền", "Xử lý", "Special"], "trunc": ["Special"]},
    "SCREW": {"type": "mechanical", "attrs": ["Size", "L", "Tiêu chuẩn", "Vật liệu", "Special"], "trunc": ["Special"]},
    "PIN": {"type": "mechanical", "attrs": ["Size", "Dung sai", "Tiêu chuẩn", "Vật liệu", "Xử lý", "Special"], "trunc": ["Special"]},
    "WASHER": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Special"], "trunc": ["Special"]},
    "SPRING": {"type": "mechanical", "attrs": ["Size", "Lực", "Vật liệu", "Special"], "trunc": ["Special"]},
    "AXIS": {"type": "mechanical", "attrs": ["Diameter", "L", "Vật liệu", "Xử lý", "Special"], "trunc": ["Special"]},
    "BEARING": {"type": "mechanical", "attrs": ["Model", "Kích thước", "Special"], "trunc": ["Special"]},
    "CIRCLIP": {"type": "mechanical", "attrs": ["Size", "Tiêu chuẩn", "Vật liệu", "Special"], "trunc": ["Special"]},
    # Nhóm Điện tử (Có API)
    "RES-SMD": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER": {"type": "electronic", "attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "Đặc tính"]},
    "DIODE": {"type": "electronic", "attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANSISTOR": {"type": "electronic", "attrs": ["Loại", "Vce", "Ic", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "IC": {"type": "electronic", "attrs": ["Chức năng", "Dải nhiệt", "Kích thước", "Special"], "trunc": ["Special", "Dải nhiệt", "Kích thước"]},
    "INDUCTOR": {"type": "electronic", "attrs": ["Giá trị", "Dòng định mức", "Kích thước", "Chuẩn", "DCR"], "trunc": ["Kích thước", "Chuẩn", "DCR"]},
    "FUSE": {"type": "electronic", "attrs": ["Dòng định mức", "Điện áp", "Kích thước"], "trunc": ["Kích thước"]},
    "CONNECTOR": {"type": "electronic", "attrs": ["Số chân", "Pitch", "Kiểu", "Special"], "trunc": ["Special"]},
    "SWITCH": {"type": "electronic", "attrs": ["Kiểu", "Rating", "Special"], "trunc": ["Special"]},
    "CABLE": {"type": "electronic", "attrs": ["Loại", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "MODULE": {"type": "electronic", "attrs": ["Tên", "Kích thước"], "trunc": ["Kích thước"]}
}

# ==========================================
# 2. CÁC HÀM XỬ LÝ (CORE ENGINE)
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
    
    # Logic cắt theo ưu tiên
    data = dict(zip(rule["attrs"], values))
    history = []
    for target in rule["trunc"]:
        if target in data:
            data.pop(target)
            history.append(target)
            new_str = f"{prefix};" + ",".join([str(v) for v in data.values() if v])
            if len(new_str) <= 40: return new_str, f"Đã lược bỏ: {','.join(history)}"
    return master_name[:37] + "...", "Cảnh báo: Vẫn vượt > 40 ký tự"

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="Check Description", layout="wide")
st.title("🛠️ Check Description")

token = get_nexar_token()
st.sidebar.write(f"API Nexar: {'✅ Kết nối' if token else '❌ Lỗi'}")

uploaded_file = st.file_uploader("Upload file BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra & Tạo báo cáo"):
        results = []
        for _, row in df.iterrows():
            desc = str(row['Mô tả/Yêu cầu kỹ thuật'])
            if ";" not in desc:
                results.append({"Status": "🔴 FAIL", "Master Name": "-", "Suggest": "-", "Note": "Sai định dạng (;)"})
                continue
            
            prefix, payload = desc.split(";", 1)
            values = payload.split(",")
            rule = MASTER_RULES.get(prefix)
            
            if not rule:
                results.append({"Status": "🟡 WARNING", "Master Name": "-", "Suggest": "-", "Note": "Chưa có quy tắc nhóm này"})
                continue
            
            # Logic xử lý
            master_name = f"{prefix};{payload}"
            suggested, note = get_truncation(prefix, rule, values)
            
            if rule["type"] == "mechanical":
                status = "🟢 PASS" if len(values) >= (len(rule["attrs"])-1) else "🔴 FAIL"
            else:
                status = "🟢 PASS" if token else "🔴 FAIL (Thiếu API)"
                
            results.append({"Status": status, "Master Name": master_name, "Suggest": suggested, "Note": note})

        res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
        st.dataframe(res_df)
        
        # Xuất file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, index=False)
        st.download_button("📥 Tải file báo cáo (.xlsx)", data=output.getvalue(), file_name="BOM_Check_Result.xlsx")
