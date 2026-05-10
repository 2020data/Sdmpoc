import streamlit as st
import time
import re

# ==========================================
# 1. 介面與全域設定
# ==========================================
st.set_page_config(page_title="SDM 臨床推理系統", page_icon="🏥", layout="wide")
st.title("🏥 醫病共享決策 (SDM) 臨床推理系統")
st.markdown("### 🔍 純 Python 規則引擎驅動 (無 API / 本地離線版)")

# ==========================================
# 2. 模擬病患 FHIR 數據庫
# ==========================================
patient_data = {
    "name": "王大明",
    "age": 65,
    "gender": "男",
    "conditions": ["高血壓", "第二型糖尿病", "輕度慢性腎臟病 (eGFR: 45)"],
    "current_medications": ["Metformin 500mg (降血糖)", "Amlodipine 5mg (降血壓)"],
    "patient_preference": "病人表示最近吞嚥大顆藥丸有困難，且非常擔心吃藥會導致腎功能惡化。"
}

with st.sidebar:
    st.header("📋 病患 FHIR 模擬資料")
    st.write(f"**姓名**：{patient_data['name']} ({patient_data['age']}歲 {patient_data['gender']})")
    st.write(f"**共病症**：{', '.join(patient_data['conditions'])}")
    st.write(f"**目前用藥**：{', '.join(patient_data['current_medications'])}")
    st.info(f"**病患主觀偏好 (Observation)**：\n{patient_data['patient_preference']}")
    st.divider()
    st.caption("🟢 系統狀態：本地規則引擎運作中")

# ==========================================
# 3. 核心邏輯：純 Python 臨床規則推理引擎 (Mock AI)
# ==========================================
def clinical_rule_engine(question, patient):
    """
    這是一個純 Python 的規則引擎，用來模擬 AI 的臨床推理。
    它會捕捉問題中的關鍵字，並比對病患的 FHIR 數據來產生結構化回覆。
    """
    response = "### 🧑‍⚕️ 藥師 SDM 臨床決策分析\n\n"
    
    # 規則 A：偵測到「血糖」或「糖尿病」相關詢問
    if re.search(r"血糖|糖尿病|降糖", question):
        response += "**【臨床數據盤點】**\n"
        response += f"- 病患患有第二型糖尿病，目前使用 {patient['current_medications'][0]}。\n"
        response += "- ⚠️ **重要警示**：病患具備輕度慢性腎臟病 (eGFR: 45)。\n\n"
        
        response += "**【SDM 處方建議與偏好對齊】**\n"
        response += "- 針對欲新增之降血糖藥物，**不建議**使用需由腎臟高比例代謝的傳統藥物 (如某些 Sulfonylureas)。\n"
        response += "- 💡 考量病患偏好：「擔心腎功能惡化」與「吞嚥困難」，建議可考慮 **SGLT2 抑制劑** (如 Empagliflozin)。\n"
        response += "  - **實證支持**：不僅能降血糖，更有明確的腎臟保護效應，精準對齊病患價值觀。\n"
        response += "  - **劑型優勢**：藥錠通常較小，符合病患的吞嚥需求。\n\n"
    
    # 規則 B：偵測到「血壓」相關詢問
    elif re.search(r"血壓|高血壓", question):
        response += "**【臨床數據盤點】**\n"
        response += f"- 病患目前使用 {patient['current_medications'][1]} 控制血壓。\n\n"
        response += "**【SDM 處方建議與偏好對齊】**\n"
        response += "- 若血壓控制未達標，考量病患有蛋白尿/慢性腎臟病風險，可評估加入 ACEI 或 ARB 類藥物。\n"
        response += "- 💡 此類藥物具備護腎效果，能回應病患「擔心腎功能惡化」的主觀焦慮。\n\n"
    
    # 預設回覆：未捕捉到特定關鍵字
    else:
        response += "**【綜合評估建議】**\n"
        response += "已接收您的臨床提問。考量病患的高血壓、糖尿病史以及 **eGFR: 45** 的腎功能限制，任何處方異動皆須特別注意腎臟清除率的劑量調整。\n\n"
        response += f"💡 此外，處方開立時請務必備註病患的特殊需求：**「{patient['patient_preference']}」**，建議優先選擇小顆粒劑型或糖漿/口溶錠。\n\n"

    response += "---\n"
    response += "🚨 **系統提示**：[⚠️需藥師進一步核實] 本結果由 Python 臨床規則引擎生成，僅供 SDM 流程參考，不可取代真實醫療決策。"
    
    return response

# 打字機特效產生器
def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)

# ==========================================
# 4. 使用者互動區塊
# ==========================================
st.markdown("### 💬 臨床藥事諮詢 (模擬輸入)")
st.caption("提示：您可以試著詢問包含「降血糖」、「高血壓」等關鍵字的問題，測試規則引擎的反應。")

user_question = st.text_input("請輸入您想評估的臨床問題：", "針對這位病患，如果要新增降血糖藥物，有什麼建議？")

if st.button("生成 SDM 建議", type="primary"):
    with st.spinner("規則引擎正在比對 FHIR 數據與實證指引中..."):
        # 模擬 AI 思考時間
        time.sleep(1) 
        
        # 呼叫純 Python 推理邏輯
        result_text = clinical_rule_engine(user_question, patient_data)
        
        # 顯示結果 (帶有打字機特效)
        st.success("推理分析完成！")
        st.write_stream(stream_data(result_text))
        
        # 人機協同：模擬數位簽章區塊
        st.divider()
        st.checkbox("我已核實上述建議，確認無臨床禁忌。(模擬醫護簽章)")

