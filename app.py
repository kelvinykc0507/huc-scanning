import streamlit as st
import os
import json
import pandas as pd
from google import genai
from PIL import Image
from datetime import datetime

# 1. 配置頁面與標題
st.set_page_config(page_title="HUC Scanning Auditor", layout="wide")
st.title("✈️ Terminal T - HUC Scanning 智能化核對系統")

# 2. 填入你免費的 Gemini API Key (來自 Google AI Studio)
GEMINI_API_KEY = "AQ.Ab8RN6K2FSvy20VIYbGRfS3W02h_DlhxNBp70dV2GkT-5qrl0A"

# 3. 設計前後端雙視窗佈局 (前線影相 vs 後台核對)
tab1, tab2 = st.tabs(["📸 前線外場 - 相片上傳", "🖥️ 辦公室 Clerk - 智能核對與導出"])

with tab1:
    st.header("ULD 金屬板相片上傳區")
    uploaded_file = st.file_uploader("請上傳或拍攝 ULD 金屬板相片...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="已上傳的相片", width=400)
        st.success("🎉 相片已成功傳送至後台，請通知內場 Clerk 進行審核。")

with tab2:
    st.header("後台自動化識別與異常處理")
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("前線原始相片")
            st.image(uploaded_file, use_container_width=True)
            
        with col2:
            st.subheader("AI 提取與風控管理")
            
            # 呼叫 Gemini 進行圖片分析
            if GEMINI_API_KEY == "YOUR_FREE_GEMINI_API_KEY" or not GEMINI_API_KEY:
                st.error("❌ 請先在 app.py 第 12 行填入你的 Gemini API Key！")
            else:
                with st.spinner("⏳ Gemini AI 正在背景分析圖片並計算信心分數..."):
                    try:
                        # 2026 最新官方 SDK 初始化方式
                        client = genai.Client(api_key=GEMINI_API_KEY)
                        img = Image.open(uploaded_file)
                        
                        prompt = """
                        Analyze this air cargo metal board image and return a JSON object with two fields:
                        1. "code": The extracted ULD container code (e.g., "PMC 94729 R7").
                        2. "confidence": A float between 0.0 and 1.0 representing your certainty.
                        Strict Rule: If blurry or unsure, provide a lower honest confidence score.
                        Return ONLY raw JSON, no markdown formatting.
                        """
                        
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=[img, prompt])
                        
                        # 清理可能帶有 markdown code block 的 response
                        res_text = response.text.strip()
                        if res_text.startswith("```json"):
                            res_text = res_text.split("```json")[1].split("```")[0].strip()
                        elif res_text.startswith("```"):
                            res_text = res_text.split("```")[1].split("```")[0].strip()
                            
                        data = json.loads(res_text)
                        
                        extracted_code = data.get("code", "").upper()
                        confidence_score = data.get("confidence", 0.0)
                        
                        st.metric(label="AI 原始預測編號", value=extracted_code)
                        st.metric(label="AI 信心分數", value=f"{confidence_score*100:.1f}%")
                        
                        # 門神把關邏輯 (Exception Handling)
                        confidence_threshold = 0.95
                        default_input_value = extracted_code
                        
                        if confidence_score < confidence_threshold:
                            st.warning("⚠️ 【觸發異常處理】AI 信心分數低於 95%！後台已自動攔截並將欄位留空，強制 Clerk 人手覆核。")
                            default_input_value = ""
                        else:
                            st.success("✅ AI 信心充足，已預填數據。")
                        
                        # 提供人手微調的 UI 介面
                        st.markdown("---")
                        final_code = st.text_input("最終入機編號 (Clerk 核對確認):", value=default_input_value)
                        final_date = st.text_input("處理日期 (Date):", value=datetime.now().strftime("%Y-%m-%d"))
                        
                        st.caption("💡 提示：如遇特殊或跨日班次，操作時請依需求手動將 Date 改為 14 號。")
                        
                        # 一鍵導出 Excel 報表
                        if st.button("📊 確認無誤，一鍵整合並導出 Master Log"):
                            log_data = [{
                                "相片名稱": uploaded_file.name,
                                "最終入機編號": final_code,
                                "AI 原始預測": extracted_code,
                                "AI 信心度": f"{confidence_score*100:.1f}%",
                                "處理日期": final_date,
                                "系統狀態": "OK" if final_code else "Pending Manual Review"
                            }]
                            df = pd.DataFrame(log_data)
                            df.to_excel("Terminal_T_Master_Log.xlsx", index=False)
                            st.balloons()
                            st.success("📊 數據已成功自動整合並導出至『Terminal_T_Master_Log.xlsx』！")
                            
                    except Exception as e:
                        st.error(f"系統運行出錯: {str(e)}")
    else:
        st.info("💡 暫時未有數據。請先去『📸 前線外場 - 相片上傳』分頁上傳一張 ULD 金屬板相片。")

# 喺網頁直接印出雲端讀到嘅 Key 開頭 7 個字，睇吓佢係咪真係 "AIzaSy"
st.write("雲端現時讀到的 Key 開頭是:", os.environ.get("GEMINI_API_KEY", "找不到 Key")[:7])