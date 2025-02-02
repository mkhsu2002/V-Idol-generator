import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import pandas as pd

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
    1: """你是一位專精於心理學、劇本創作的虛擬偶像人設專家。
請使用繁體中文回應。
根據以下描述來設計虛擬偶像的人設參數框架：
{input_text}

請以表格方式列出以下類別和對應的參數名稱：
1. 基本個資
2. 性格特徵
3. 外觀描述
4. 興趣愛好
5. 背景故事""",

    2: """你是一位專精於心理學與數據建模的虛擬偶像人設專家。
請使用繁體中文回應。
根據以下人設框架，請針對每個類別展開更詳細的子參數：

{previous_result}""",

    3: """你是一位心理學與創意寫作專家。
請使用繁體中文回應。
根據以下參數細目，請為每個參數生成具體的例子：

{previous_result}""",

    4: """你是一位理解理論的心理學專家。
請使用繁體中文回應。
根據以下特徵進行行為模式分析，並提供優化建議：

{previous_result}""",

    5: """請使用繁體中文回應。
根據以下分析，重新調整並生成更細緻的人物描述：

{previous_result}""",

    6: """你是一位專業的角色設計師。
請使用繁體中文回應，並提供英文對照。
根據以下人設資料，請提供三組外觀描述，包含：
1. 五官特徵
2. 髮型設計
3. 整體風格
強調寫實人像風格，4K高解析度：

{previous_result}"""
}

def generate_response(prompt):
    try:
        messages = [
            {
                "role": "system",
                "content": "你是一位專業的虛擬偶像設計助手，請使用繁體中文回應。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"生成過程發生錯誤: {str(e)}")
        return None

def get_full_prompt(step, input_text="", previous_result=""):
    """生成完整提示詞"""
    if step == 1:
        return BASE_PROMPTS[step].format(input_text=input_text)
    else:
        return BASE_PROMPTS[step].format(previous_result=previous_result)

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

def auto_generate_all():
    """自動生成所有步驟"""
    with st.spinner("自動生成中..."):
        for step in range(st.session_state.current_step, 7):
            # 獲取當前步驟的提示詞
            current_prompt = get_full_prompt(
                step,
                st.session_state.input_text,
                st.session_state.results[f'step{step-1}'] if step > 1 else ""
            )
            
            # 生成結果
            result = generate_response(current_prompt)
            if result:
                st.session_state.results[f"step{step}"] = result
            else:
                st.error(f"步驟 {step} 生成失敗")
                break
        
        # 更新當前步驟到最後
        st.session_state.current_step = 6
        st.rerun()

def main():
    st.title("FlyPig V-Idol 人設生成器")
    
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
                    full_prompt = get_full_prompt(current_step, st.session_state.input_text, st.session_state.results[f'step{current_step-1}'] if current_step > 1 else "")
                    
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
            
            col2_1, col2_2 = st.columns(2)
            
            with col2_1:
                if st.button("生成下一步", disabled=current_step > 6):
                    with st.spinner("生成中..."):
                        result = generate_response(st.session_state.prompts[current_step])
                        if result:
                            st.session_state.results[f"step{current_step}"] = result
                            if current_step < 6:
                                st.session_state.current_step += 1
                            st.rerun()
            
            with col2_2:
                if st.button("自動完成所有步驟", disabled=current_step > 6):
                    auto_generate_all()
            
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