import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & QUY TẮC (MASTER RULES)
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

# TOÀN BỘ DANH MỤC LINH KIỆN ĐIỆN TỬ (PHỤ LỤC 1)
MASTER_RULES = {
    # --- NHÓM ĐIỆN TRỞ (RESISTOR) ---
    "RES-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-VR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-SPECIAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-ARRAY": {"attrs": ["Giá trị", "Sai số", "Công suất", "Kích thước", "Đặc tính nhiệt", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},

    # --- NHÓM TỤ ĐIỆN (CAPACITOR) ---
    "CAP-CER SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-ALUM SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-CER DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-ALUM DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-MICA SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-MICA DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-SUPER": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-ARRAY": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},

    # --- NHÓM DIODE ---
    "DIODE-SWITCHING": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-SCHOTTKY": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-ARRAY": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-RECTIFIER": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-BRIDGE": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-SURGE ABSORBER": {"attrs": ["Điện áp", "Dòng xả", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-FAST": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-VAR": {"attrs": ["Điện áp", "Điện dung", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "DIODE-ZENER": {"attrs": ["Điện áp", "Công suất", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},

    # --- NHÓM TRANSISTOR / FET ---
    "TRANS-BJT": {"attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANS-POWER": {"attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANS-DIGITAL": {"attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "MOS-FET": {"attrs": ["Loại kênh", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANS-BJT ARRAY": {"attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANS-BJT Pre-Bias": {"attrs": ["Loại", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "MOS-FET ARRAY": {"attrs": ["Loại kênh", "Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "RF-FET": {"attrs": ["Loại", "Tần số", "Điện áp", "Công suất", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANS-RF": {"attrs": ["Loại", "Tần số", "Điện áp", "Công suất", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "JFET": {"attrs": ["Loại", "Điện áp", "Công suất", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},

    # --- NHÓM IC ---
    "IC": {"attrs": ["Chức năng", "Kích thước", "Dải nhiệt", "Special"], "trunc": ["Special", "Dải nhiệt", "Kích thước"]},

    # --- NHÓM LED & DISPLAY ---
    "LED-SMD": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Màu sắc"], "trunc": ["Kích thước"]},
    "LED-DIP": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Màu sắc"], "trunc": ["Kích thước"]},
    "LED-IR": {"attrs": ["Kích thước"], "trunc": ["Kích thước"]},
    "LED-MATRIX": {"attrs": ["Cấu hình", "Kích thước", "Màu sắc", "Điện áp", "Kết nối trong"], "trunc": ["Kết nối trong", "Kích thước"]},
    "LED-7SEG": {"attrs": ["Số digit", "Cỡ chữ", "Điện áp", "Dòng điện", "Kích thước", "Màu sắc"], "trunc": ["Kích thước", "Màu sắc"]},

    # --- NHÓM FILTER, CRYSTAL, OSCILLATOR ---
    "FILTER-SMD": {"attrs": ["Loại", "Tần số", "Điện dung", "Kích thước", "Điện áp", "Special"], "trunc": ["Kích thước", "Special"]},
    "FILTER-DIP": {"attrs": ["Loại", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "CRYSTAL": {"attrs": ["Tần số", "Sai số", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "OSCILLATOR": {"attrs": ["Tần số", "Sai số", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},

    # --- NHÓM CONNECTOR, SWITCH, THERMISTOR ---
    "CONN-SMD": {"attrs": ["Số chân", "Pitch", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "CONN-DIP": {"attrs": ["Số chân", "Pitch", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "CONN-SPECIAL": {"attrs": ["Đặc tính", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "SWITCH": {"attrs": ["Loại", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "PUSH-BUTTON": {"attrs": ["Loại", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "THERMISTOR": {"attrs": ["Loại", "Giá trị", "Sai số", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},

    # --- NHÓM INDUCTOR (CUỘN CẢM) ---
    "IND-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "DCR", "Dòng điện", "Chuẩn"], "trunc": ["Chuẩn", "Kích thước", "DCR"]},
    "IND-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "DCR", "Dòng điện", "Chuẩn"], "trunc": ["Chuẩn", "Kích thước", "DCR"]},
    "IND-VR": {"attrs": ["Giá trị", "Dòng điện", "DCR"], "trunc": ["DCR"]},
    "IND-ARRAY": {"attrs": ["Giá trị", "Kích thước", "DCR"], "trunc": ["Chuẩn", "Kích thước", "DCR"]},
    "IND-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Số lượng"], "trunc": ["Chuẩn", "Số lượng", "Sai số"]},

    # --- NHÓM RELAY, TRANSFORMER, FUSE ---
    "RELAY": {"attrs": ["Dòng điện cuộn", "Điện áp DC", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TRANSFORMER": {"attrs": ["Loại", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "FUSE": {"attrs": ["Dòng định mức", "Điện áp", "Kích thước"], "trunc": ["Kích thước"]},
    "FUSE-CLIP": {"attrs": ["Loại", "Điện áp", "Kích thước", "Dòng định mức"], "trunc": ["Kích thước"]},
    "FUSE-COVER": {"attrs": ["Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},

    # --- NHÓM ESD, TVS, FERRITE BEAD ---
    "ESD": {"attrs": ["Điện dung", "Điện áp làm việc", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TVS-DIODE": {"attrs": ["Công suất", "Điện áp", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TVS-HYRIST": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "TVS-VARISTOR": {"attrs": ["Điện áp", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "FB": {"attrs": ["Trở kháng", "Dòng điện", "Kích thước", "DCR"], "trunc": ["Kích thước", "DCR"]},

    # --- NHÓM MODULE, CHOKE, ATTENUATOR, OTHERS ---
    "MODULE DIP": {"attrs": ["Tên", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "MODULE SMD": {"attrs": ["Tên", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "LCD MODULE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "MIC MODULE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "RECEIVER MODULE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "CAMERA MODULE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "SPEAKER MODULE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "CHOKE SMD": {"attrs": ["Trở kháng", "Dòng điện", "DCR", "Kích thước"], "trunc": ["Kích thước", "DCR"]},
    "CHOKE DIP": {"attrs": ["Trở kháng", "Dòng điện", "Kích thước", "DCR"], "trunc": ["Kích thước", "DCR"]},
    "ATTENUATOR": {"attrs": ["Spec", "Dòng điện", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "THYRISTOR": {"attrs": ["Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "THERMOSTAT": {"attrs": ["Nhiệt độ", "Kích thước", "Special"], "trunc": ["Special"]},
    "FAN": {"attrs": ["Điện áp", "Công suất", "Kích thước", "Special"], "trunc": ["Special", "Kích thước"]},
    "LED HOLDER": {"attrs": ["Kích thước", "Màu sắc", "Special"], "trunc": ["Special"]},
    "LAMP": {"attrs": ["Điện áp AC", "Kích thước", "Màu sắc"], "trunc": ["Kích thước"]},
    "MEMORY CARDS": {"attrs": ["Loại", "Dung lượng", "Special"], "trunc": ["Special"]},

    # --- NHÓM CONTACTOR, BREAKER, CABLE, WIRE ---
    "CONTACTOR": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Special"], "trunc": ["Special"]},
    "AUXILLARY CONTACT": {"attrs": ["Tiếp điểm", "Số cực", "Special"], "trunc": ["Special"]},
    "MCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Special"], "trunc": ["Special"]},
    "MCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Special"], "trunc": ["Special"]},
    "RCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Special"], "trunc": ["Special"]},
    "ELCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Special"], "trunc": ["Special"]},
    "USB CABLE": {"attrs": ["Số đầu giắc", "Loại giắc", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "BUNCHED CABLE": {"attrs": ["Loại giắc", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "HIGHT FREQUENCY CABLE": {"attrs": ["Số đầu giắc", "Loại giắc", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "CONT CABLE": {"attrs": ["Số đầu giắc", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "COAXIAL CABLE": {"attrs": ["Đường kính", "Trở kháng", "Chiều dài", "Special"], "trunc": ["Special", "Chiều dài"]},
    "CONDUCTOR WIRE": {"attrs": ["Loại", "Kích thước", "Màu sắc", "Special"], "trunc": ["Special"]},
    "FERRITE": {"attrs": ["Kích thước", "Special"], "trunc": ["Special"]},

    # --- NHÓM NON-STANDARD, PCB, TERMINAL ---
    "MOTOR": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "WINDOW": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "CHARGER": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "EARPHONE": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "ADAPTER": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "ANTENNA": {"attrs": ["Info", "Kích thước"], "trunc": ["Kích thước"]},
    "BARE PCB ARRAY": {"attrs": ["Model", "Version"], "trunc": ["Kích thước"]},
    "SMD FINAL": {"attrs": ["Model", "Version"], "trunc": ["Kích thước"]},
    "PHA FINAL": {"attrs": ["Model", "Version"], "trunc": ["Kích thước"]},
    "COMPRESSION TERMINAL": {"attrs": ["Vật liệu", "Model", "Special"], "trunc": ["Special"]},
    "VINYL INSULATED TERMINAL": {"attrs": ["Loại", "Model", "Màu sắc", "Special"], "trunc": ["Special"]}
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

def get_api_description(mpn, token, prefix):
    """
    HÀM GỌI API THỰC TẾ: Bắt buộc lấy dữ liệu từ Nexar.
    Bạn cần chèn query GraphQL vào khu vực này.
    """
    if not token or pd.isna(mpn) or str(mpn).strip() == "": 
        return None
    
    # --- KHU VỰC CHÈN LỆNH GRAPHQL CỦA BẠN ---
    # Ví dụ: 
    # response = requests.post(url, json={"query": f"...{mpn}..."})
    # Lấy dữ liệu từ response và ghép thành chuỗi.
    
    # GIẢ LẬP KẾT QUẢ API (Thay thế bằng code thật khi bạn có)
    return f"{prefix};API_Val1,API_Val2,API_Val3" 

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
        with st.spinner("Đang kết nối API và xử lý dữ liệu..."):
            results = []
            for _, row in df.iterrows():
                desc = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
                mpn = str(row.get('Mã NSX', '')).strip() # BẮT BUỘC có Mã NSX để chạy API
                
                if ";" not in desc:
                    results.append({"Status": "🔴 FAIL", "Master Name": "-", "Suggest": "-", "Note": "Sai format (;)"})
                    continue
                
                prefix, payload = desc.split(";", 1)
                values_from_excel = [v.strip() for v in payload.split(",")]
                rule = MASTER_RULES.get(prefix)
                
                if not rule:
                    results.append({"Status": "🟡 WARNING", "Master Name": "-", "Suggest": "-", "Note": "Chưa có quy tắc"})
                    continue
                
                # BẮT BUỘC GỌI API CHO MỌI LINH KIỆN TRONG MASTER_RULES
                api_desc = get_api_description(mpn, token, prefix)
                
                if api_desc:
                    # Nếu API trả về dữ liệu -> Lấy làm chuẩn
                    master_name = api_desc
                    # Tách các thuộc tính từ chuỗi API để đưa vào động cơ gọt chữ
                    try:
                        values_for_trunc = api_desc.split(";", 1)[1].split(",")
                        suggested, note = get_truncation(prefix, rule, values_for_trunc)
                        status = "🟢 PASS" # Trạng thái dựa trên việc API trả về kết quả tốt
                    except Exception as e:
                        suggested, note = "-", "Lỗi tách chuỗi từ API"
                        status = "🔴 FAIL"
                else:
                    # Nếu API không có dữ liệu hoặc lỗi
                    master_name = f"{prefix};{payload}"
                    suggested, note = get_truncation(prefix, rule, values_from_excel)
                    status = "🔴 FAIL (Không tìm thấy API/Thiếu Mã NSX)"
                    
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
