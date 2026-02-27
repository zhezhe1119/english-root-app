import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import json

# --- 1. 頁面配置 ---
st.set_page_config(page_title="英文字根分解器", layout="wide", page_icon="📑")

# --- 2. 自定義 CSS (高度還原專業深色樣式) ---
st.markdown("""
    <style>
    /* 全域背景 */
    .stApp { background-color: #0E1117; color: white; }
    
    /* 側邊欄樣式 */
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    
    /* 狀態框樣式 (綠色區塊) */
    .status-success {
        background-color: #163020;
        border-radius: 6px;
        padding: 12px 15px;
        color: #FFFFFF;
        font-weight: 500;
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .status-success::before { content: '✅'; margin-right: 10px; }

    /* 資訊排版樣式 */
    .info-row { margin-bottom: 12px; font-size: 1.05rem; }
    .info-label { color: #FFFFFF; font-weight: bold; }
    .info-content { color: #FFFFFF; }

    /* 藍色 AI 提示框 */
    .info-box-blue {
        background-color: #0C1D33;
        border: 1px solid #1F6FEB;
        padding: 15px;
        border-radius: 8px;
        color: #58A6FF;
        margin-bottom: 15px;
    }
    
    /* 本地字根標籤樣式 */
    .root-tag-box {
        background-color: #163020;
        padding: 15px;
        border-radius: 6px;
        color: #4ADE80;
        font-family: monospace;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 讀取資料 ---
@st.cache_data
def load_data():
    csv_file = '大考中心分級字彙.CSV'
    if os.path.exists(csv_file):
        for enc in ['utf-8-sig', 'big5', 'gbk']:
            try:
                df = pd.read_csv(csv_file, encoding=enc)
                df.columns = [c.strip() for c in df.columns]
                return df
            except:
                continue
    return None

df_vocab = load_data()

# --- 4. 擴充字根辭庫 ---
WORD_ROOTS = {
    # 字首 (Prefixes)
    'anti': '反對、對抗 (against)', 'auto': '自我 (self)', 'bi': '二 (two)',
    'co': '共同 (together)', 'de': '向下、去除 (down/remove)', 'dis': '不、相反 (not/opposite)',
    'ex': '向外、前任 (out/former)', 'inter': '之間 (between)', 'mis': '錯誤 (wrong)',
    'non': '非、不 (not)', 'pre': '預先 (before)', 're': '再次、往回 (again/back)',
    'sub': '在下面 (under)', 'super': '在上面、超越 (above/over)', 'trans': '穿越 (across)',
    'un': '不、否定 (not)', 'tri': '三 (three)', 'uni': '一 (one)',
    # 字根 (Roots)
    'ann': '年 (year)', 'audi': '聽 (listen)', 'bio': '生命 (life)', 
    'cept': '拿、取 (take/seize)', 'cede': '行進、讓步 (go/yield)', 'circ': '環、圓 (circle)',
    'dict': '說 (say/speak)', 'duc': '引導 (lead)', 'form': '形狀 (shape)',
    'graph': '寫、畫 (write/draw)', 'ject': '投、擲 (throw)', 'manu': '手 (hand)',
    'mob': '移動 (move)', 'port': '搬運 (carry)', 'pos': '放置 (put/place)',
    'rupt': '破裂 (break)', 'scribe': '寫 (write)', 'spec': '看 (look/see)',
    'struct': '建立 (build)', 'vid': '看 (see)', 'viv': '活 (live)',
    'voc': '聲音 (voice)', 'path': '感情 (feel/suffer)', 'phil': '愛 (love)',
    # 字尾 (Suffixes)
    'able': '能夠...的 (can be done)', 'al': '關於...的 (pertaining to)', 'er': '人、物 (person/thing)',
    'ful': '充滿...的 (full of)', 'ion': '行為、過程 (act/process)', 'ism': '主義、信念 (belief/ism)',
    'ist': '專家、人 (specialist)', 'ity': '狀態、性質 (state/quality)', 'less': '沒有 (without)',
    'ly': '地、狀態 (how something is)', 'ment': '行為、結果 (action/result)', 'ness': '性質、狀態 (state/quality)'
}

# --- 5. 側邊欄 ---
with st.sidebar:
    st.markdown("### ⚙️ 設定面板")
    api_key = st.text_input("請輸入 Google API Key", type="password")
    st.markdown("---")
    st.markdown("""
        <div style='color: #8B949E; font-size: 0.9rem;'>
        <b>使用說明：</b><br>
        1. 從 <a href="https://aistudio.google.com/" style="color:#58A6FF; text-decoration:none;">Google AI Studio</a> 取得 API Key。<br>
        2. 沒有 API Key 時，仍可搜尋詞彙資訊。
        3. 注意API Key的安全性，請勿公開分享，且有免費使用額度。        
        </div>
    """, unsafe_allow_html=True)

# --- 6. 主介面 ---
st.title("📑 英文字根分解器")
st.write("結合大考中心分級字彙庫與 Gemini 2.5 AI 智慧模型，深入解析單字字根構成。")

query = st.text_input("🔍 請輸入要分解的英文單字：", value="import").strip().lower()

if query:
    st.markdown("---")
    col1, col2 = st.columns(2)

    # --- 左側：詞彙查詢結果 ---
    with col1:
        st.subheader("📑 詞彙查詢結果")
        if df_vocab is not None:
            res = df_vocab[df_vocab['word'].str.lower() == query] if 'word' in df_vocab.columns else pd.DataFrame()
            
            if not res.empty:
                st.markdown('<div class="status-success">詞彙中有該單字</div>', unsafe_allow_html=True)
                exclude = ['id', 'ID', 'createdAt', 'CreatedAt', 'word', 'Word', 'created_at']
                item_data = res.iloc[0].to_dict()
                
                # 1. 等級顯示
                level = item_data.get('level', item_data.get('Level', 'N/A'))
                st.markdown(f'<div class="info-row"><span class="info-label">等級：</span><span class="info-content">Level {level}</span></div>', unsafe_allow_html=True)
                
                # 2. 詞性顯示
                raw_pos = str(item_data.get('pos', item_data.get('POS', item_data.get('part_of_speech', 'N/A'))))
                formatted_pos = raw_pos.replace('.', '. / ').strip().rstrip('/')
                st.markdown(f'<div class="info-row"><span class="info-label">詞性：</span><span class="info-content">{formatted_pos}</span></div>', unsafe_allow_html=True)
                
                # 3. 中文意思顯示
                meaning = item_data.get('chinese', item_data.get('Chinese', item_data.get('definition', 'N/A')))
                st.markdown(f'<div class="info-row"><span class="info-label">中文意思：</span><span class="info-content">{meaning}</span></div>', unsafe_allow_html=True)
                
                # 自動顯示其餘隱藏欄位
                displayed_keys = ['level', 'Level', 'pos', 'POS', 'part_of_speech', 'chinese', 'Chinese', 'definition'] + exclude
                for k, v in item_data.items():
                    if k not in displayed_keys:
                        st.markdown(f'<div class="info-row"><span class="info-label">{k}：</span><span class="info-content">{v}</span></div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 大考中心分級字庫中查無此單字，已轉由 AI 解析字根結構。")

    # --- 右側：AI 解析區 ---
    with col2:
        st.subheader("🤖 AI 解析/詞根詳解")
        if not api_key:
            st.markdown('<div class="info-box-blue">⚠️ 目前使用本地字根分析（基礎模式），請輸入 API Key 啟動 AI 深度解析</div>', unsafe_allow_html=True)
            found_components = [f"<b>{root}</b> → {mean}" for root, mean in WORD_ROOTS.items() if root in query]
            if found_components:
                st.markdown("🔍 **偵測到可能的字根組件：**")
                for comp in found_components:
                    st.markdown(f'<div class="root-tag-box">{comp}</div>', unsafe_allow_html=True)
            else:
                st.caption("本地字典查無匹配字根組件。")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash') 
                with st.spinner("AI 正在深度分析字根構成..."):
                    # 已移除「原始語義與演變」以及「例句」的要求
                    prompt = f"請詳細拆解英文單字 '{query}' 的字根、字首、字尾，並簡潔說明各部分的含義。請使用繁體中文回答，不需要提供原始語義演變或例句。"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 解析失敗: {e}")

st.markdown("---")
