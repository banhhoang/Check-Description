import streamlit as st
import pandas as pd
import requests
import io
import re

# ==========================================
# 1. CẤU HÌNH & QUY TẮC (MASTER RULES)
# ==========================================
CLIENT_ID = "cab894db-95f3-47e4-8348-90417571c8b5"
CLIENT_SECRET = "-bZfWortFB-YS31GCwAw47rqCIHg7IyhmIKC"

NEXAR_MAPPING = {
    "Giá trị": ["resistance", "capacitance", "inductance"],
    "Sai số": ["tolerance"],
    "Kích thước": ["package / case", "case/package", "case code - mm", "size / dimension"],
    "Công suất": ["power (watts)", "power rating", "power"],
    "Điện áp": ["voltage rating", "voltage - rated", "voltage - dc reverse (vr) (max)", "voltage"],
    "Đặc tính": ["temperature coefficient", "features"],
    "ESR": ["equivalent series resistance"],
    "Dòng điện": ["current rating", "current - average rectified (io)", "current"],
}

# TOÀN BỘ DANH MỤC ĐIỆN TỬ TỪ PHỤ LỤC 1 (KHÔNG BỎ SÓT BẤT KỲ LINH KIỆN NÀO)
MASTER_RULES = {
    # --- NHÓM ĐIỆN TRỞ (RESISTOR) ---
    "RES-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-VR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-SPECIAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-ARRAY": {"attrs": ["Giá trị", "Sai số", "Công suất", "Kích thước", "Đặc tính nhiệt", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},

    # --- NHÓM TỤ ĐIỆN (CAPACITOR) - CHUẨN DẤU PHẨY TỪ ẢNH ---
    "CAP-CER,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP ALUM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-CER,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP ALUM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP MICA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-MICA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
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
# 2. CÁC HÀM XỬ LÝ (CORE & API) - ĐÃ NÂNG CẤP
# ==========================================
def get_nexar_token():
    url = "https://identity.nexar.com/connect/token"
    payload = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    try:
        r = requests.post(url, data=payload, timeout=5)
        return r.json().get("access_token")
    except: return None

def normalize_for_fuzzy_match(s):
    """Làm sạch ký tự để máy tính dò TÌM luật gốc (Giúp nhận dạng khi kỹ sư gõ sai)"""
    return re.sub(r'[^A-Z0-9]', '', str(s).upper())

def get_api_description(mpn, token, actual_prefix, rule):
    """Bắn Part Number lên API và đúc khuôn Mô tả chuẩn - Nâng cấp bắt lỗi API"""
    if not token or pd.isna(mpn) or str(mpn).strip() == "": 
        return "NO_MPN"
    
    url = "https://api.nexar.com/graphql"
    # Dùng supSearch thay vì supSearchMpn để tìm kiếm rộng và chuẩn xác hơn
    query = """
    query Search($mpn: String!) {
      supSearch(q: $mpn, limit: 1) {
        results {
          part {
            mpn
            specs {
              attribute { name }
              value
            }
          }
        }
      }
    }
    """
    try:
        response = requests.post(
            url, 
            headers={"Authorization": f"Bearer {token}"}, 
            json={"query": query, "variables": {"mpn": mpn}},
            timeout=10
        )
        data = response.json()
        
        # Bắt lỗi nếu Nexar từ chối truy vấn (Ví dụ token hết hạn, query sai)
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown API Error")
            return f"API_ERROR: {error_msg}"
            
        results = data.get("data", {}).get("supSearch", {}).get("results", [])
        
        if not results: 
            return "NOT_FOUND_ON_NEXAR"
        
        part_specs = results[0].get("part", {}).get("specs", [])
        spec_dict = {spec["attribute"]["name"].lower(): spec["value"] for spec in part_specs}
        
        api_values = []
        for attr in rule["attrs"]:
            val = ""
            if attr == "Chuẩn":
                val = "Auto" if "aec-q200" in str(spec_dict).lower() else ""
            else:
                mapped_keys = NEXAR_MAPPING.get(attr, [])
                for key in mapped_keys:
                    if key in spec_dict:
                        val = str(spec_dict[key]).strip().replace(" ", "")
                        val = val.replace("µ", "u").replace("μ", "u").replace("Ω", "OHM")
                        break
            api_values.append(val if val else "N/A")
            
        return f"{actual_prefix};" + ",".join(api_values)
    except Exception as e:
        return f"CODE_ERROR: {str(e)}"

def get_truncation(prefix, rule, values):
    """Thuật toán gọt chữ theo Phụ lục"""
    master_name = f"{prefix};" + ",".join(values)
    if len(master_name) <= 40: return master_name, ""
    
    data = dict(zip(rule["attrs"], values))
    history = []
    for target in rule["trunc"]:
        if target in data:
            data.pop(target)
            history.append(target)
            new_str = f"{prefix};" + ",".join([str(v) for v in data.values() if v])
            if len(new_str) <= 40: return new_str, f"(Đã gọt: {','.join(history)})"
    return master_name[:37] + "...", "(Cảnh báo: Vẫn > 40 ký tự)"

# ==========================================
# 3. GIAO DIỆN & VÒNG LẶP KIỂM DUYỆT KHẮT KHE
# ==========================================
st.set_page_config(page_title="Check Description", layout="wide")
st.title("🛠️ Check Description (Strict QC Mode)")
st.markdown("---")

st.sidebar.header("System Status")
token = get_nexar_token()
st.sidebar.metric("API Nexar", "Connected" if token else "Disconnected", delta=None)

uploaded_file = st.file_uploader("📂 Upload file BOM (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra & Đối chiếu API"):
        with st.spinner("Đang kết nối API và đối chiếu dữ liệu..."):
            results = []
            for _, row in df.iterrows():
                # 1. NHẬN DỮ LIỆU GỐC TỪ KỸ SƯ
                desc = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
                mpn = str(row.get('Mã NSX', '')).strip()
                
                if ";" not in desc:
                    results.append({"Status": "🔴 FAIL", "Mô tả API": "-", "Suggest": "-", "Note": "Lỗi format: Thiếu dấu chấm phẩy (;)"})
                    continue
                
                raw_user_prefix = desc.split(";", 1)[0]
                
                # 2. DÒ TÌM LUẬT (Để nhận biết kỹ sư đang viết linh kiện gì)
                actual_prefix = ""
                rule = None
                for key, r in MASTER_RULES.items():
                    if normalize_for_fuzzy_match(raw_user_prefix) == normalize_for_fuzzy_match(key):
                        actual_prefix = key
                        rule = r
                        break
                
                # NẾU KHÔNG CÓ LUẬT -> BÁO LỖI FAIL LUÔN NHƯ YÊU CẦU
                if not rule:
                    results.append({"Status": "🔴 FAIL", "Mô tả API": "-", "Suggest": "-", "Note": f"Sai tiền tố: '{raw_user_prefix}' không tồn tại trong danh mục chuẩn (Phụ lục 1)"})
                    continue
                
                # 3. LẤY MÔ TẢ TỪ API LÀM CHUẨN
                api_desc = get_api_description(mpn, token, actual_prefix, rule)
                
                # XỬ LÝ LỖI TỪ BỘ MÁY API
                if api_desc == "NO_MPN":
                    results.append({"Status": "🔴 FAIL", "Mô tả API": "-", "Suggest": "-", "Note": "Dòng này bị bỏ trống Mã NSX nên không thể tra cứu API"})
                elif api_desc == "NOT_FOUND_ON_NEXAR":
                    results.append({"Status": "🟡 UNVERIFIED", "Mô tả API": "-", "Suggest": "-", "Note": f"Hệ thống Nexar API không có dữ liệu cho mã NSX: {mpn}"})
                elif str(api_desc).startswith("API_ERROR:") or str(api_desc).startswith("CODE_ERROR:"):
                    results.append({"Status": "🔴 FAIL", "Mô tả API": "-", "Suggest": "-", "Note": f"Lỗi hệ thống Nexar: {api_desc}"})
                else:
                    # NẾU API TRẢ VỀ CHUỖI THÀNH CÔNG -> CHẤM ĐIỂM
                    values_for_trunc = api_desc.split(";", 1)[1].split(",")
                    suggested, trunc_note = get_truncation(actual_prefix, rule, values_for_trunc)
                    
                    if desc == api_desc:
                        if len(desc) > 40:
                            status = "🟡 WARNING"
                            note = f"Mô tả đúng cấu trúc API nhưng vượt 40 ký tự. Vui lòng copy ở cột Suggest. {trunc_note}"
                        else:
                            status = "🟢 PASS"
                            note = "Khớp 100% với dữ liệu hãng"
                    else:
                        status = "🔴 FAIL"
                        # Chỉ lỗi cho kỹ sư biết vì sao FAIL
                        if raw_user_prefix != actual_prefix:
                            note = f"Sai chuẩn Tiền tố (Của bạn: '{raw_user_prefix}' | Chuẩn: '{actual_prefix}')"
                        elif desc.replace(" ", "") == api_desc.replace(" ", ""):
                            if desc.upper() == api_desc.upper():
                                note = "Lỗi khoảng trắng: Thừa/thiếu dấu cách so với bản chuẩn API"
                            else:
                                note = "Lỗi chữ hoa/chữ thường (Case Sensitivity)"
                        else:
                            note = "Thông số mô tả không khớp với thông số thực tế của Mã NSX từ API"
                            
                    results.append({"Status": status, "Mô tả API": api_desc, "Suggest": suggested, "Note": note})

            # Xuất báo cáo
            res_df = pd.concat([df, pd.DataFrame(results)], axis=1)
            st.success("Hoàn tất đối chiếu 100% dữ liệu với API!")
            st.dataframe(res_df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("📥 Tải file báo cáo (.xlsx)", data=output.getvalue(), file_name="BOM_Check_API_Result.xlsx")
