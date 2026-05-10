import streamlit as st
import time
import re
from pypdf import PdfReader

# ==========================================
# 1. 介面與全域設定
# ==========================================
st.set_page_config(page_title="SDM 文獻對話系統", page_icon="🏥", layout="wide")
st.title("🏥 醫病共享決策 (SDM) 文獻對話系統")
st.markdown("### 🔍 純 Python 微型 RAG 資料庫與臨床規則引擎")

# 初始化對話歷史紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 加入歡迎詞
    st.session_state.messages.append({"role": "assistant", "content": "您好！我是 SDM 臨床輔助系統。請先在左側檢視病患資料，並上傳相關的 PDF 藥典或仿單，然後就可以開始問我問題囉！"})

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
    
    # ------------------------------------------
    # PDF 文獻上傳與資料庫建置
    # ------------------------------------------
    st.header("📚 建立本地文獻資料庫")
    uploaded_pdf = st.file_uploader("上傳 PDF (仿單/指引/文獻)", type=["pdf"])
    
    pdf_sentences = [] # 存放切塊後的文獻段落
    if uploaded_pdf is not None:
        with st.spinner("正在建立文獻索引庫..."):
            reader = PdfReader(uploaded_pdf)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text: full_text += text + "\n"
            
            # 微型 RAG 核心：將文章透過句號、換行符號切分成獨立段落 (Chunking)
            # 這樣之後搜尋才能精準抓出上下文
            raw_sentences = re.split(r'[。！？\n]', full_text)
            pdf_sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]
            
            st.success(f"✅ 資料庫建置完成！共擷取 {len(pdf_sentences)} 個文獻段落。")

# ==========================================
# 3. 核心邏輯：微型 RAG 檢索與對話生成器
# ==========================================
def retrieve_and_generate(question, patient, sentences_db):
    """
    純 Python 的微型檢索增強生成 (RAG) 引擎。
    結合意圖識別、文獻檢索與預設臨床規則。
    """
    # 1. 意圖與關鍵字擴展 (Intent Recognition & Keyword Expansion)
    search_keywords = []
    if re.search(r"副作用|不良反應|不舒服", question):
        search_keywords.extend(["副作用", "不良反應", "發生率", "症狀", "噁心", "暈眩"])
    if re.search(r"劑量|怎麼吃|用法", question):
        search_keywords.extend(["劑量", "用法", "口服", "mg", "每日", "調整"])
    if re.search(r"禁忌|不能吃|注意", question):
        search_keywords.extend(["禁忌", "避免", "不建議", "慎用", "警告"])
    if re.search(r"腎|eGFR|洗腎", question):
        search_keywords.extend(["腎", "eGFR", "清除率", "透析", "肌酸酐"])
    
    # 如果沒有特定關鍵字，就用提問本身的字詞去比對 (簡化版)
    if not search_keywords:
        # 移除常見的停用詞，提取長度大於2的詞作為檢索詞
        words = re.findall(r'\w{2,}', question)
        search_keywords.extend(words)

    # 2. 文獻檢索比對 (Text Retrieval / Matching)
    retrieved_snippets = []
    if sentences_db and search_keywords:
        for i, sentence in enumerate(sentences_db):
            if any(kw in sentence for kw in search_keywords):
                # 抓取命中段落的「上一句」與「下一句」提供上下文 (Windowing)
                start = max(0, i - 1)
                end = min(len(sentences_db), i + 2)
                snippet = "。".join(sentences_db[start:end]) + "。"
                if snippet not in retrieved_snippets:
                    retrieved_snippets.append(snippet)
                if len(retrieved_snippets) >= 3: # 最多只取前 3 個最相關的段落
                    break

    # 3. 組合回覆 (Generation)
    response = ""
    
    # -- 區塊 A：文獻比對結果 --
    if retrieved_snippets:
        response += "🔍 **【文獻資料庫檢索結果】**\n"
        response += f"根據您上傳的 PDF，我為您找到以下與「*{', '.join(search_keywords[:3])}*」相關的段落：\n\n"
        for idx, snippet in enumerate(retrieved_snippets):
            response += f"> 📄 *節錄 {idx+1}：* \"...{snippet}...\"\n\n"
    elif sentences_db:
        response += "🔍 **【文獻資料庫檢索結果】**\n"
        response += "在您上傳的 PDF 中，沒有直接找到與您提問完全相符的關鍵字段落。\n\n"

    # -- 區塊 B：臨床規則與 SDM 護欄 --
    response += "🩺 **【臨床 SDM 綜合建議】**\n"
    if re.search(r"血糖|降糖|Metformin", question):
        response += f"- **用藥現況**：病患目前使用 {patient['current_medications'][0]}。\n"
        response += "- ⚠️ **護欄警示**：病患具備輕度慢性腎臟病 (eGFR: 45)。若需調整劑量，請特別留意腎功能限制。\n"
        response += f"- 💡 **偏好對齊**：病患有「{patient['patient_preference']}」的狀況。建議優先考慮 SGLT2 抑制劑，護腎且劑型小。\n"
    elif re.search(r"血壓|降壓|Amlodipine", question):
        response += f"- **用藥現況**：病患目前使用 {patient['current_medications'][1]} 控制血壓。\n"
        response += "- 💡 **護腎評估**：考量慢性腎臟病風險，可評估加入 ACEI/ARB 類藥物以保護腎功能。\n"
    else:
        response += f"考量病患的高血壓、糖尿病史及 **eGFR: 45**，任何處方異動須特別注意腎臟清除率。\n"
        response += f"請將病患需求：**「{patient['patient_preference']}」** 納入決策考量。\n"

    response += "\n---\n🚨 **系統提示**：[⚠️需藥師進一步核實] 此建議由本地純 Python 文字比對引擎生成，僅供 POC 展示。"
    return response

# 打字機特效產生器
def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# ==========================================
# 4. 對話介面渲染 (Chat UI)
# ==========================================
# 顯示歷史對話紀錄
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 處理使用者新提問
if prompt := st.chat_input("請輸入您想查詢的臨床問題 (例如：這個藥有什麼副作用？腎功能不好可以吃嗎？)"):
    # 顯示使用者提問
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 系統產生回應
    with st.chat_message("assistant"):
        with st.spinner("正在檢索文獻庫並進行臨床推理..."):
            # 模擬思考時間
            time.sleep(0.8) 
            
            # 呼叫微型 RAG 引擎
            result_text = retrieve_and_generate(prompt, patient_data, pdf_sentences)
            
            # 以打字機效果印出
            st.write_stream(stream_data(result_text))
            
    # 將系統回應加入歷史紀錄
    st.session_state.messages.append({"role": "assistant", "content": result_text})

