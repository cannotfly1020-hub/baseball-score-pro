import json
import base64
from google import genai
from google.genai import types
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# 独立させたモジュールから読み込み
from prompts.pitching_prompts import PITCHER_PROMPT
from utils.pitching_utils import enhance_sharpness, calculate_pitcher_stats_from_grid, create_pitcher_excel_from_compiled, IP_OPTIONS, DECISION_OPTIONSimport io

st.set_page_config(
    page_title="投手成績解析＆エディタ",
    page_icon="🛡️",
    layout="wide"
)

# 打撃アプリ完全共通のチームカラーUIデザイン
st.markdown("""
<style>
/* 1. 背景：天然芝の深緑 */
.stApp {
    background-color: #0f1f17 !important;
    color: #f0f4f1 !important;
}

/* 2. スマホ上部スペース */
.block-container {
    padding-top: 3.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
}

/* 3. タブバー：金色アンダーライン */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    overflow-x: auto !important;
    white-space: nowrap !important;
    padding: 8px 4px 10px 4px !important;
    background-color: transparent !important;
    border-bottom: 2.5px solid #d4af37 !important;
    -webkit-overflow-scrolling: touch;
    margin-bottom: 1rem !important;
}

/* 4. 非選択タブ */
.stTabs [data-baseweb="tab"] {
    height: auto !important;
    min-height: 40px !important;
    padding: 8px 14px !important;
    border-radius: 8px 8px 0 0 !important;
    background-color: #1b382b !important;
    color: #c2d6cb !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border: 1px solid #2d5a45 !important;
    border-bottom: none !important;
    display: inline-flex !important;
    align-items: center !important;
}

/* 5. 選択中タブ：ユニフォーム赤 ＋ 金色枠 */
.stTabs [aria-selected="true"] {
    background-color: #991b1b !important;
    color: #ffffff !important;
    border-top: 2.5px solid #d4af37 !important;
    border-left: 2px solid #d4af37 !important;
    border-right: 2px solid #d4af37 !important;
    border-bottom: none !important;
    font-weight: bold !important;
}

h1, h2, h3, h4 {
    color: #ffffff !important;
}

/* 6. アップローダー */
[data-testid="stFileUploader"] {
    background-color: #172d22 !important;
    border: 1px dashed #d4af37 !important;
    border-radius: 10px !important;
    padding: 10px !important;
}

/* 7. 投手カード枠：スコア白 ＋ 赤金ストライプ */
div[data-testid="stForm"] {
    background-color: #ffffff !important;
    border: 1px solid #dcd6cd !important;
    border-left: 6px solid #991b1b !important;
    border-radius: 8px !important;
    padding: 14px 12px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

div[data-testid="stForm"] label,
div[data-testid="stForm"] h5 {
    color: #111111 !important;
    font-weight: bold !important;
}

/* 8. スマホキーボード完全防止 */
div[data-baseweb="select"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
    user-select: none !important;
}
div[data-baseweb="select"] {
    cursor: pointer !important;
}

/* 9. 保存ボタン */
div[data-testid="stForm"] button {
    background-color: #991b1b !important;
    color: #ffffff !important;
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    font-size: 0.95rem !important;
    padding: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}
div[data-testid="stForm"] button * {
    color: #ffffff !important;
}

/* 10. 固定画像ビューワー */
.sticky-mobile-viewer {
    position: -webkit-sticky;
    position: sticky;
    top: 3.5rem;
    z-index: 99;
    background-color: rgba(15, 31, 23, 0.95);
    padding: 8px;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
    border: 1px solid #d4af37;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

if "all_pitchers_data" not in st.session_state:
    st.session_state.all_pitchers_data = {}
if "pitcher_images_b64" not in st.session_state:
    st.session_state.pitcher_images_b64 = {}

api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini APIキー", type="password")
client = genai.Client(api_key=api_key) if api_key else None

st.title("🛡️ 相手攻撃面（守備）スコア解析＆投手エディタ")
st.caption("赤丸失点・赤線被安打・K・四死球をAIが自動集計し、自軍投手成績を算出します（相手選手名は完全除外）。")

uploaded_files = st.file_uploader(
    "相手攻撃面（自チーム守備）スコア写真を選択（複数選択可）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files and client:
    if st.button("AIで投手成績（赤丸失点・被安打等）を一括解析する", type="primary"):
        prog = st.progress(0)
        status = st.empty()
        for idx, f in enumerate(uploaded_files):
            status.text(f"【{idx+1}/{len(uploaded_files)}】{f.name} を解析中...")
            raw_b = f.read()
            st.session_state.pitcher_images_b64[f.name] = base64.b64encode(raw_b).decode()
            highres = enhance_sharpness(Image.open(io.BytesIO(raw_b)))
            try:
                res = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_bytes(data=highres, mime_type="image/jpeg"),
                        "自チーム投手の投球成績（赤丸失点・赤線被安打・奪三振・球数）を抽出してください。"
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=PITCHER_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                st.session_state.all_pitchers_data[f.name] = json.loads(res.text)
            except Exception as e:
                st.error(f"{f.name} 解析エラー: {e}")
            prog.progress((idx + 1) / len(uploaded_files))
        status.empty()
        st.success("🎉 投手データの解析が完了しました！")

if st.session_state.all_pitchers_data:
    st.divider()
    m_files = list(st.session_state.all_pitchers_data.keys())
    c1, c2 = st.columns([2, 1])
    sel_file = c1.selectbox("📁 確認・編集する試合スコア", m_files)
    is_sticky = c2.checkbox("📱 スマホ表示（画像を上部に固定）", value=False)

    cur_pitchers = st.session_state.all_pitchers_data.get(sel_file, [])
    cur_b64 = st.session_state.pitcher_images_b64.get(sel_file, "")

    col_img, col_form = st.columns([1.1, 1.3])
    with col_img:
        st.markdown(f"#### 📷 原本画像: `{sel_file}`")
        zoom = st.slider("🔍 拡大率", 100, 350, 150, 25, format="%d%%")
        b_h = 320 if is_sticky else 620
        viewer_html = f"""
        <div class="{'sticky-mobile-viewer' if is_sticky else ''}" style="width:100%; height:{b_h}px; overflow:auto; border:2px solid #555; border-radius:8px; background-color:#222; text-align:center;">
            <img src="data:image/jpeg;base64,{cur_b64}" style="width:{zoom}%; max-width:none; cursor:grab;" />
        </div>
        """
        components.html(viewer_html, height=b_h + 20)

    with col_form:
        st.markdown("#### 🎯 投手成績エディタ")
        st.caption("タブを指で横にスワイプして投手を選択し、修正後は「保存」を押してください。")

        if st.button("➕ この試合に投手枠を手動追加"):
            st.session_state.all_pitchers_data[sel_file].append({
                "pitcher_name": "投手", "uniform_number": "", "innings_pitched": 3.0,
                "pitch_count": 50, "hits_allowed": 0, "strikeouts": 0, "walks_allowed": 0,
                "hit_by_pitch": 0, "runs_allowed": 0, "earned_runs": 0, "decision": "なし"
            })
            st.rerun()

        pt_tabs = st.tabs([f"#{p.get('uniform_number','')} {p.get('pitcher_name','投手')}" for p in cur_pitchers])
        for idx, (tab, pt) in enumerate(zip(pt_tabs, cur_pitchers)):
            with tab:
                with st.form(key=f"form_pt_{sel_file}_{idx}"):
                    st.markdown(f"##### **#{pt.get('uniform_number','-')} {pt.get('pitcher_name','投手')}**")
                    
                    fc1, fc2, fc3 = st.columns([1, 2, 2])
                    u_num = fc1.text_input("背番号", value=str(pt.get("uniform_number","")), key=f"num_{sel_file}_{idx}")
                    p_name = fc2.text_input("投手名（漢字）", value=str(pt.get("pitcher_name","")), key=f"name_{sel_file}_{idx}")
                    dec_idx = DECISION_OPTIONS.index(pt.get("decision","なし")) if pt.get("decision","なし") in DECISION_OPTIONS else 0
                    dec = fc3.selectbox("勝敗結果", DECISION_OPTIONS, index=dec_idx, key=f"dec_{sel_file}_{idx}")

                    s1, s2, s3, s4 = st.columns(4)
                    cur_ip = float(pt.get("innings_pitched", 0.0))
                    ip_idx = IP_OPTIONS.index(cur_ip) if cur_ip in IP_OPTIONS else 0
                    ip_val = s1.selectbox("投球回(IP)", IP_OPTIONS, index=ip_idx, key=f"ip_{sel_file}_{idx}")
                    pc = s2.number_input("投球数", 0, 200, int(pt.get("pitch_count", 0)), key=f"pc_{sel_file}_{idx}")
                    ha = s3.number_input("被安打(赤線)", 0, 30, int(pt.get("hits_allowed", 0)), key=f"ha_{sel_file}_{idx}")
                    so = s4.number_input("奪三振", 0, 30, int(pt.get("strikeouts", 0)), key=f"so_{sel_file}_{idx}")

                    s5, s6, s7, s8 = st.columns(4)
                    bb = s5.number_input("与四球", 0, 20, int(pt.get("walks_allowed", 0)), key=f"bb_{sel_file}_{idx}")
                    hbp = s6.number_input("与死球", 0, 20, int(pt.get("hit_by_pitch", 0)), key=f"hbp_{sel_file}_{idx}")
                    ra = s7.number_input("失点(赤丸)", 0, 30, int(pt.get("runs_allowed", 0)), key=f"ra_{sel_file}_{idx}")
                    er = s8.number_input("自責点", 0, 30, int(pt.get("earned_runs", 0)), key=f"er_{sel_file}_{idx}")

                    st.write("")
                    if st.form_submit_button("💾 この投手の変更を保存", use_container_width=True):
                        st.session_state.all_pitchers_data[sel_file][idx] = {
                            "uniform_number": u_num, "pitcher_name": p_name, "innings_pitched": ip_val,
                            "pitch_count": pc, "hits_allowed": ha, "strikeouts": so,
                            "walks_allowed": bb, "hit_by_pitch": hbp, "runs_allowed": ra,
                            "earned_runs": er, "decision": dec
                        }
                        st.success(f"{p_name} 投手のデータを保存しました！")
                        st.rerun()

                if st.button(f"🗑️ この投手枠（{pt.get('pitcher_name','投手')}）を削除", key=f"del_{sel_file}_{idx}"):
                    st.session_state.all_pitchers_data[sel_file].pop(idx)
                    st.rerun()

        st.write("")
        if st.button("📊 全投手の成績を集計確定する", type="primary", use_container_width=True):
            compiled_pt = []
            for mf, p_list in st.session_state.all_pitchers_data.items():
                compiled_pt.extend(calculate_pitcher_stats_from_grid(p_list, match_file_name=mf))
            st.session_state["compiled_pitchers"] = compiled_pt
            st.success("🎉 全投手の成績を確定しました！「ホーム」画面で統合結果を確認できます。")
