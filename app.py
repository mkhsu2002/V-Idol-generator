import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# 載入環境變數
load_dotenv()

# 設定 OpenAI 客戶端
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("請在 .env 檔案中設定 OPENAI_API_KEY")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# 定義基礎提示詞
BASE_PROMPTS = {
    1: """你是一位專精於心理學、劇本創作的虛擬偶像人設專家。根據"{input_text}"為基礎參考來設計一個虛擬偶像的人設參數框架，須含括以下參數：基本個資、性格特徵、外觀描述、興趣愛好、背景故事等，並以表格方式列出每個類別和對應的參數名稱。""",
    2: """你是一位專精於心理學與數據建模的虛擬偶像人設專家，致力於打造具高度實用性的人設資料。根據以下虛擬偶像的人設參數框架，請針對每個類別展開更詳細的子參數，確保參數可供後續 LLM 微調使用：""",
    3: """你是一位心理學與創意寫作專家，擅長為虛擬偶像設計人設資料。根據以下虛擬偶像的人設參數細目，請為每個參數生成具體的例子，確保範例具有創造性、貼近現代受眾，並涵蓋多樣性：""",
    4: """你是一位理解理論的心理學專家，針對一群具有最基本特徵的人類，根據以下的特徵進行行為模式的分析，並針對明確的問題進行優化建議：""",
    5: """根據檢查到的問題及優化建議，重新調整生成一份更細緻的人類行為描述：""",
    6: """你是一位公關造型設計師，擅長為偶像設計符合大眾喜愛具有人緣的造型。根據以上優化後的人設資料，請寫出三種適合外觀生成的提示詞，對人物的五官及髮型有詳盡描述，分別提供中文及英文，強調寫實人像，4K高解析："""
}

def generate_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"生成過程發生錯誤: {str(e)}")
        return None

def save_results_to_file(results, step):
    """將結果儲存為JSON檔案"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vidol_step{step}_{timestamp}.json"
    
    data = {
        "step": step,
        "content": results[f"step{step}"],
        "timestamp": timestamp
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename

def save_complete_results(results):
    """儲存完整的人設參數集"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vidol_complete_{timestamp}.json"
    
    data = {
        "timestamp": timestamp,
        "basic_description": st.session_state.input_text,
        "steps": {
            f"step{i}": results[f"step{i}"] for i in range(1, 7)
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename

def main():
    st.title("V-Idol 人設生成器")
    
    # 初始化 session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'results' not in st.session_state:
        st.session_state.results = {f"step{i}": "" for i in range(1, 7)}
    if 'prompts' not in st.session_state:
        st.session_state.prompts = {}
    if 'input_text' not in st.session_state:
        st.session_state.input_text = "一個在溫哥華長大的華裔陽光大男孩，30歲就創業成功財務自由，開始環遊世界邊寫作的人生。"

    # 使用 columns 分割上下兩部分
    top_section, bottom_section = st.container(), st.container()

    with top_section:
        st.markdown("### 操作區域")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 輸入區域
            st.session_state.input_text = st.text_area(
                "請輸入基礎描述",
                value=st.session_state.input_text,
                height=100
            )
            
            # 當前步驟狀態
            st.write(f"當前步驟: {st.session_state.current_step}/6")
            
            # 顯示並允許編輯當前步驟的提示詞
            current_step = st.session_state.current_step
            if current_step <= 6:
                with st.expander(f"步驟 {current_step} 提示詞", expanded=True):
                    # 組合完整提示詞
                    if current_step == 1:
                        full_prompt = BASE_PROMPTS[current_step].format(input_text=st.session_state.input_text)
                    else:
                        full_prompt = BASE_PROMPTS[current_step]
                        if current_step > 1:
                            full_prompt += f"\n\n{st.session_state.results[f'step{current_step-1}']}"
                    
                    # 允許編輯提示詞
                    edited_prompt = st.text_area(
                        "編輯提示詞",
                        value=full_prompt,
                        height=150,
                        key=f"prompt_{current_step}"
                    )
                    st.session_state.prompts[current_step] = edited_prompt
        
        with col2:
            # 生成按鈕
            st.write("")  # 空行對齊
            st.write("")  # 空行對齊
            if st.button("生成下一步", disabled=current_step > 6):
                with st.spinner("生成中..."):
                    result = generate_response(st.session_state.prompts[current_step])
                    if result:
                        st.session_state.results[f"step{current_step}"] = result
                        if current_step < 6:
                            st.session_state.current_step += 1
                        st.rerun()
            
            # 完整下載按鈕（只在完成所有步驟後顯示）
            if all(st.session_state.results.values()):
                if st.button("下載完整人設參數集", type="primary"):
                    filename = save_complete_results(st.session_state.results)
                    st.success(f"完整人設參數集已儲存至 {filename}")

    # 分隔線
    st.markdown("---")

    with bottom_section:
        st.markdown("### 生成結果")
        
        # 使用 tabs 顯示各步驟結果
        tabs = st.tabs([f"步驟 {i}" for i in range(1, 7)])
        for i, tab in enumerate(tabs, 1):
            with tab:
                result = st.session_state.results[f"step{i}"]
                if result:
                    # 允許編輯結果
                    edited_result = st.text_area(
                        "編輯結果",
                        value=result,
                        height=300,
                        key=f"result_step{i}"
                    )
                    st.session_state.results[f"step{i}"] = edited_result
                    
                    # 單步驟下載按鈕
                    if st.button(f"下載步驟 {i} 結果", key=f"download_step{i}"):
                        filename = save_results_to_file(st.session_state.results, i)
                        st.success(f"結果已儲存至 {filename}")
                else:
                    st.info("尚未生成結果")

if __name__ == "__main__":
    main() 