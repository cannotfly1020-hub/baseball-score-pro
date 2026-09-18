import io
import json
import base64
from datetime import datetime
import pandas as pd
from google import genai
from google.genai import types
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageEnhance

# ----------------------------------------------------
# ページ初期設定
# ----------------------------------------------------
st.set_page_config(
    page_title="投手成績解析＆エディタ",
    page_icon="⚾️",
    layout="wide",
)

# ----------------------------------------------------
# チームカラー UIデザイン（打撃・ホーム画面と完全統一）
# ----------------------------------------------------
st.markdown("""
<style>
/* 1. 画面全体の背景：天然芝の深緑 */
.stApp {
    background-color: #0f1f17 !important;
    color: #f0f4f1 !important;
}

/* 2. スマホ上部メニューバーとの重なりを防ぐ上部スペース */
.block-container {
    padding-top: 3.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
}

/* 3. タブバー外枠：金色アンダーライン */
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

/* 6. 見出し・タイトルの装飾 */
h1, h2, h3, h4 {
    color: #ffffff !important;
}

/* 7. ファイルアップローダー */
[data-testid="stFileUploader"] {
    background-color: #172d22 !important;
    border: 1px dashed #d4af37 !important;
    border-radius: 10px !important;
    padding: 10px !important;
}

/* 8. 選手カード枠：スコア用紙白 ＋ 赤金ストライプ枠 */
div[data-testid="stForm"] {
    background-color: #ffffff !important;
    border: 1px solid #dcd6cd !important;
    border-left: 6px solid #991b1b !important;
    border-radius: 8px !important;
    padding: 16px 14px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35) !important;
}

div[data-testid="stForm"] h5,
div[data-testid="stForm"] label,
div[data-testid="stForm"] label p,
div[data-testid="stForm"] span,
div[data-testid="stForm"] p {
    color: #111111 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

/* 9. 入力欄（テキスト・数値）：白背景・黒文字・見やすいグレー枠 */
div[data-testid="stForm"] input[type="text"],
div[data-testid="stForm"] input[type="number"] {
    background-color: #f8faf9 !important;
    color: #111111 !important;
    font-weight: bold !important;
    border: 1.5px solid #b0bec5 !important;
    border-radius: 6px !important;
}

div[data-testid="stForm"] [data-testid="stNumberInput"] button {
    background-color: #e2e8f0 !important;
    border: 1px solid #cbd5e1 !important;
    color: #1e293b !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] [data-testid="stNumberInput"] button * {
    color: #1e293b !important;
    fill: #1e293b !important;
}

/* 10. セレクトボックス（白地・黒文字） */
div[data-testid="stForm"] div[data-baseweb="select"],
div[data-testid="stForm"] div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #2d5a45 !important;
    border-radius: 6px !important;
    min-height: 38px !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] * {
    color: #111111 !important;
    font-weight: bold !important;
}
div[data-baseweb="select"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
    user-select: none !important;
}
div[data-baseweb="select"] {
    cursor: pointer !important;
}

/* 11. ヘッダータグ（ピッチャー情報ブロック） */
.pitcher-stat-header {
    text-align: center;
    background-color: #1b382b !important;
    color: #ffffff !important;
    font-weight: bold;
    font-size: 0.85rem;
    padding: 5px 0;
    border-radius: 6px;
    margin-bottom: 6px;
    border-bottom: 2.5px solid #d4af37;
}

/* 12. アクションボタン */
div[data-testid="stForm"] button[kind="secondaryFormSubmit"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"] {
    background-color: #991b1b !important;
    color: #ffffff !important;
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    font-size: 0.95rem !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}
div[data-testid="stForm"] button[kind="secondaryFormSubmit"] *,
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-secondary"] * {
    color: #ffffff !important;
}

/* 13. 固定画像ビューワー */
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

/* ===================================================
   全端末共通：サイドバーの「app」を「🏠 ホーム」に置換
   =================================================== */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a {
    position: relative !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a *,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child span,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child p {
    color: transparent !important;
    opacity: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a::after {
    content: "🏠 ホーム" !important;
    position: absolute !important;
    left: 0.75rem !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 0.95rem !important;
    font-weight: bold !important;
    color: #ffffff !important;
    opacity: 1 !important;
    pointer-events: none !important;
    white-space: nowrap !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a[aria-selected="true"]::after {
    color: #ffd700 !important;
}

/* ===================================================
   PCモニター表示専用（横幅768px以上）の最適化
   =================================================== */
@media (min-width: 768px) {
    .block-container {
        padding-top: 2.0rem !important;
        padding-bottom: 2.0rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1400px !important;
    }

    div[data-testid="stCaptionContainer"] p {
        color: #e0ece5 !important;
        font-size: 1.0rem !important;
        font-weight: 500 !important;
    }

    .stApp > div p, .stApp > div span {
        color: #f0f4f1 !important;
    }

    hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border-color: #2d5a45 !important;
    }

    /* PCカード内の文字色強制固定 */
    div[data-testid="stForm"] h5,
    div[data-testid="stForm"] h5 *,
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] p *,
    div[data-testid="stForm"] span,
    div[data-testid="stForm"] strong {
        color: #111111 !important;
    }

    /* サイドバー全体の背景・枠・文字色 */
    section[data-testid="stSidebar"] {
        width: 180px !important;
        min-width: 180px !important;
        border-right: 3px solid #d4af37 !important;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.5) !important;
    }
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background-color: #801212 !important;
    }
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    section[data-testid="stSidebar"] [aria-selected="true"] span,
    section[data-testid="stSidebar"] [aria-selected="true"] p {
        color: #ffd700 !important;
        font-weight: bold !important;
    }

    /* 開閉ボタン本体（枠線を金色・背景透明化） */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button,
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] button {
        background-color: transparent !important;
        background: transparent !important;
        border: 1.5px solid #d4af37 !important;
        border-radius: 6px !important;
        padding: 4px 6px !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stSidebarHeader"] button * {
        color: #ffd700 !important;
        fill: #ffd700 !important;
        stroke: #ffd700 !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="stSidebarCollapsedControl"] button:hover,
    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebarHeader"] button:hover {
        background-color: rgba(212, 175, 55, 0.2) !important;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.5) !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 内部ヘルパー関数（画像鮮鋭化・Excel生成・集計）
# ----------------------------------------------------
def enhance_sharpness_pitcher(pil_img: Image.Image) -> bytes:
    """原本画像をAI解析用に鮮鋭化"""
    enhancer = ImageEnhance.Sharpness(pil_img)
    sharpened = enhancer.enhance(2.0)
    buf = io.BytesIO()
    sharpened.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

PITCHING_PROMPT = """
あなたはスコアブック解析の専門家です。
スコアブック下部または右側に記載されている「投球成績欄（投手成績）」を走査し、
登板した投手全員のデータを以下のJSONフォーマットで漏れなく抽出してください。

出力形式（JSON配列）:
[
  {
    "order": 1,
    "uniform_number": "1",
    "player_name": "投手氏名",
    "role": "先発",
    "result": "勝",
    "innings_pitched": 4,
    "innings_fraction": "0",
    "pitch_count": 68,
    "batters_faced": 18,
    "hits_allowed": 3,
    "hr_allowed": 0,
    "strikeouts": 5,
    "walks": 2,
    "hit_by_pitch": 0,
    "wild_pitches": 0,
    "runs_allowed": 1,
    "earned_runs": 1,
    "highlight": ""
  }
]
※ 登板順に抽出し、roleは「先発」「救援」「抑え」、resultは「勝」「敗」「Ｓ」「なし」から判定してください。
※ innings_fractionは "0", "1/3", "2/3" から選択してください。
"""

def create_pitching_excel(compiled_data):
    """投手通算成績および試合別一覧のExcel作成"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_all = pd.DataFrame(compiled_data)
        df_all.to_excel(writer, sheet_name='全試合投手成績詳細', index=False)

        # 投手別通算サマリー作成
        if not df_all.empty and "選手名" in df_all.columns:
            summary = df_all.groupby(["背番号", "選手名"]).agg(
                登板数=("試合名", "count"),
                投球回合計=("投球回(数値)", "sum"),
                合計球数=("投球数", "sum"),
                奪三振=("奪三振", "sum"),
                与四球=("与四球", "sum"),
                被安打=("被安打", "sum"),
                失点=("失点", "sum"),
                自責点=("自責点", "sum"),
                勝利=("勝敗", lambda x: (x == "勝").sum()),
                敗戦=("勝敗", lambda x: (x == "敗").sum()),
                セーブ=("勝敗", lambda x: (x == "Ｓ").sum())
            ).reset_index()

            # 防御率計算（学童野球基準：7回換算）
            summary["防御率"] = summary.apply(
                lambda r: round((r["自責点"] * 7) / r["投球回合計"], 2) if r["投球回合計"] > 0 else 0.00,
                axis=1
            )
            summary.to_excel(writer, sheet_name='投手別通算成績サマリー', index=False)

    return output.getvalue()

# ----------------------------------------------------
# セッション状態の初期化
# ----------------------------------------------------
if "all_pitchers_data" not in st.session_state:
    st.session_state.all_pitchers_data = {}
if "pitcher_match_images_b64" not in st.session_state:
    st.session_state.pitcher_match_images_b64 = {}

# APIキー設定
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("管理者APIキー (Gemini)", type="password")

client = genai.Client(api_key=api_key) if api_key else None

st.subheader("⚾️ スコア照合・投手成績エディタ")
st.caption("高精細カラー解析により、投球数・投球回数・奪三振・与四死球・失点・自責点を精査します。")

# ----------------------------------------------------
# バックアップ読み込み（JSON完全復元）
# ----------------------------------------------------
with st.expander("📂 前回の作業バックアップ（JSON）を読み込んで再開する", expanded=False):
    backup_file = st.file_uploader(
        "保存した投手成績バックアップJSONファイルを選択",
        type=["json"],
        key="pitcher_backup_uploader"
    )
    if backup_file is not None:
        if st.button("このバックアップから作業を完全復元する", type="secondary", use_container_width=True):
            try:
                loaded_data = json.loads(backup_file.getvalue().decode("utf-8"))
                if "all_pitchers_data" in loaded_data:
                    st.session_state.all_pitchers_data = loaded_data["all_pitchers_data"]
                    st.session_state.pitcher_match_images_b64 = loaded_data.get("pitcher_match_images_b64", {})
                    st.success(f"🎉 全 {len(st.session_state.all_pitchers_data)} 試合分の投手データを完全に復元しました！")
                    st.rerun()
                else:
                    st.error("バックアップファイルの形式が正しくありません。")
            except Exception as e:
                st.error(f"バックアップ復元エラー: {e}")

st.divider()

if not client:
    st.warning("Gemini APIキーを設定してください（Secrets または サイドバー）。")
    st.stop()

uploaded_files = st.file_uploader(
    "投手成績を解析するスコアブック写真を選択（複数ファイル可）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="pitcher_uploader"
)

if uploaded_files:
    if st.button(f"AIで全{len(uploaded_files)}試合の投手成績を一括解析する", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        new_all_pitchers = {}
        new_images_b64 = {}

        for idx, f in enumerate(uploaded_files):
            f_name = f.name
            status_text.text(f"【{idx+1}/{len(uploaded_files)}】{f_name} の投手成績欄を高精度解析中...")
            raw_bytes = f.read()
            new_images_b64[f_name] = base64.b64encode(raw_bytes).decode()
            
            pil_img = Image.open(io.BytesIO(raw_bytes))
            highres_bytes = enhance_sharpness_pitcher(pil_img)

            try:
                res_pitching = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_bytes(data=highres_bytes, mime_type="image/jpeg"),
                        "このスコアブックから、各投手の登板順、氏名、背番号、投球回数、球数、被安打、三振、四球、失点、自責点を高精度に読み取ってください。"
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=PITCHING_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                parsed = json.loads(res_pitching.text)
                new_all_pitchers[f_name] = parsed
            except Exception as e:
                st.error(f"{f_name} の投手解析エラー: {e}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.empty()
        if new_all_pitchers:
            st.session_state.all_pitchers_data = new_all_pitchers
            st.session_state.pitcher_match_images_b64 = new_images_b64
            st.success(f"🎉 全 {len(new_all_pitchers)} 試合分の投手解析が完了しました！")

# ----------------------------------------------------
# データが存在する場合の編集エディタ & 保存
# ----------------------------------------------------
if st.session_state.all_pitchers_data:
    st.divider()

    # バックアップダウンロード
    current_backup_payload = {
        "all_pitchers_data": st.session_state.all_pitchers_data,
        "pitcher_match_images_b64": st.session_state.pitcher_match_images_b64,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    json_string = json.dumps(current_backup_payload, ensure_ascii=False, indent=2)

    st.download_button(
        label="💾 現在の作業状態をバックアップ保存 (JSONダウンロード)",
        data=json_string,
        file_name=f"学童野球投手スコア_途中データ_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

    match_files = list(st.session_state.all_pitchers_data.keys())
    
    top_c1, top_c2 = st.columns([2, 1])
    selected_match_file = top_c1.selectbox("📁 確認・編集する試合を選択", match_files, key="pitcher_match_select")
    is_mobile_sticky = top_c2.checkbox("📱 スマホ表示（画像を上部に固定）", value=False, key="pitcher_sticky_chk")

    current_pitchers = st.session_state.all_pitchers_data.get(selected_match_file, [])
    current_b64 = st.session_state.pitcher_match_images_b64.get(selected_match_file, "")

    add_col1, add_col2 = st.columns([1, 3])
    with add_col1:
        if st.button("➕ この試合に投手を手動追加"):
            new_pitcher_template = {
                "order": len(current_pitchers) + 1,
                "uniform_number": "",
                "player_name": f"追加投手{len(current_pitchers) + 1}",
                "role": "救援" if current_pitchers else "先発",
                "result": "なし",
                "innings_pitched": 1,
                "innings_fraction": "0",
                "pitch_count": 15,
                "batters_faced": 4,
                "hits_allowed": 1,
                "hr_allowed": 0,
                "strikeouts": 1,
                "walks": 0,
                "hit_by_pitch": 0,
                "wild_pitches": 0,
                "runs_allowed": 0,
                "earned_runs": 0,
                "highlight": ""
            }
            st.session_state.all_pitchers_data[selected_match_file].append(new_pitcher_template)
            st.rerun()

    # 左右分割比率 [0.9, 1.6]
    col_img, col_grid = st.columns([0.9, 1.6])

    with col_img:
        st.markdown(f"#### 📷 原本画像: `{selected_match_file}`")
        zoom_val = st.slider("🔍 拡大率", min_value=100, max_value=350, value=150, step=25, format="%d%%", key="pitcher_zoom")
        
        box_height = 320 if is_mobile_sticky else 500
        sticky_class = "sticky-mobile-viewer" if is_mobile_sticky else ""

        # マウスドラッグ移動（パン操作）対応ビューワー
        viewer_html = f"""
        <div id="drag-viewer-pitcher" class="{sticky_class}" style="
            width: 100%; 
            height: {box_height}px; 
            overflow: auto; 
            border: 2px solid #d4af37; 
            border-radius: 8px; 
            background-color: #111; 
            cursor: grab; 
            user-select: none;
            -webkit-user-select: none;
        ">
            <img id="pitcher-score-img" src="data:image/jpeg;base64,{current_b64}" style="
                width: {zoom_val}%; 
                max-width: none; 
                display: block; 
                margin: 0 auto; 
                pointer-events: none;
            " />
        </div>

        <script>
            const ele = document.getElementById('drag-viewer-pitcher');
            let pos = {{ top: 0, left: 0, x: 0, y: 0 }};

            const mouseDownHandler = function (e) {{
                ele.style.cursor = 'grabbing';
                pos = {{
                    left: ele.scrollLeft,
                    top: ele.scrollTop,
                    x: e.clientX,
                    y: e.clientY,
                }};
                document.addEventListener('mousemove', mouseMoveHandler);
                document.addEventListener('mouseup', mouseUpHandler);
            }};

            const mouseMoveHandler = function (e) {{
                const dx = e.clientX - pos.x;
                const dy = e.clientY - pos.y;
                ele.scrollTop = pos.top - dy;
                ele.scrollLeft = pos.left - dx;
            }};

            const mouseUpHandler = function () {{
                ele.style.cursor = 'grab';
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
            }};

            ele.addEventListener('mousedown', mouseDownHandler);
        </script>
        """
        components.html(viewer_html, height=box_height + 25)

    with col_grid:
        st.markdown("#### 🎯 投手成績盤面エディタ")
        st.caption("タブを指で横にスワイプして投手を選択し、修正後は「保存」を押してください。")

        tab_labels = []
        for idx, pitcher in enumerate(current_pitchers):
            u_num = str(pitcher.get("uniform_number", "")).strip()
            num_str = f"#{u_num} " if u_num else ""
            p_name = str(pitcher.get("player_name", "投手")).strip()
            role_tag = f"({pitcher.get('role', '登板')})"
            tab_labels.append(f"{num_str}{p_name}{role_tag}")

        pitcher_tabs = st.tabs(tab_labels)

        for idx, (p_tab, pitcher) in enumerate(zip(pitcher_tabs, current_pitchers)):
            with p_tab:
                u_num_init = str(pitcher.get("uniform_number", "")).strip()
                p_name_init = str(pitcher.get("player_name", "")).strip()
                role_init = pitcher.get("role", "先発")
                res_init = pitcher.get("result", "なし")

                with st.form(key=f"form_pitcher_{selected_match_file}_{idx}"):
                    st.markdown(f"##### **【登板{idx+1}】 #{u_num_init or '-'} {p_name_init} （{role_init}）**")

                    # 基本情報
                    r_c1, r_c2, r_c3, r_c4 = st.columns([1, 2, 1.2, 1.2])
                    u_num = r_c1.text_input("背番号", value=u_num_init, key=f"p_num_{selected_match_file}_{idx}")
                    p_name = r_c2.text_input("選手名（漢字）", value=p_name_init, key=f"p_name_{selected_match_file}_{idx}")
                    role_options = ["先発", "救援", "抑え"]
                    role_idx = role_options.index(role_init) if role_init in role_options else 0
                    role_val = r_c3.selectbox("役割", role_options, index=role_idx, key=f"p_role_{selected_match_file}_{idx}")
                    
                    res_options = ["なし", "勝", "敗", "Ｓ"]
                    res_idx = res_options.index(res_init) if res_init in res_options else 0
                    res_val = r_c4.selectbox("勝敗", res_options, index=res_idx, key=f"p_res_{selected_match_file}_{idx}")

                    # 投球回・球数・打者数
                    st.markdown("<div class='pitcher-stat-header'>⚾️ 投球イニング・投球数・対戦打者</div>", unsafe_allow_html=True)
                    s_c1, s_c2, s_c3, s_c4 = st.columns(4)
                    inn_full = s_c1.number_input("投球回 (完了回)", min_value=0, max_value=15, value=int(pitcher.get("innings_pitched", 0)), key=f"p_inn_{selected_match_file}_{idx}")
                    frac_opts = ["0", "1/3", "2/3"]
                    frac_init = str(pitcher.get("innings_fraction", "0"))
                    frac_idx = frac_opts.index(frac_init) if frac_init in frac_opts else 0
                    inn_frac = s_c2.selectbox("端数回", frac_opts, index=frac_idx, key=f"p_frac_{selected_match_file}_{idx}")
                    p_count = s_c3.number_input("投球数 (球数)", min_value=0, max_value=200, value=int(pitcher.get("pitch_count", 0)), step=1, key=f"p_cnt_{selected_match_file}_{idx}")
                    bf_val = s_c4.number_input("対戦打者数", min_value=0, max_value=60, value=int(pitcher.get("batters_faced", 0)), step=1, key=f"p_bf_{selected_match_file}_{idx}")

                    # 被安打・三振・四球・死球
                    st.markdown("<div class='pitcher-stat-header'>📊 奪三振・与四死球・被安打・失点詳細</div>", unsafe_allow_html=True)
                    d_c1, d_c2, d_c3, d_c4, d_c5, d_c6 = st.columns(6)
                    h_val = d_c1.number_input("被安打", min_value=0, max_value=30, value=int(pitcher.get("hits_allowed", 0)), key=f"p_h_{selected_match_file}_{idx}")
                    so_val = d_c2.number_input("奪三振", min_value=0, max_value=30, value=int(pitcher.get("strikeouts", 0)), key=f"p_so_{selected_match_file}_{idx}")
                    bb_val = d_c3.number_input("与四球", min_value=0, max_value=30, value=int(pitcher.get("walks", 0)), key=f"p_bb_{selected_match_file}_{idx}")
                    hbp_val = d_c4.number_input("与死球", min_value=0, max_value=20, value=int(pitcher.get("hit_by_pitch", 0)), key=f"p_hbp_{selected_match_file}_{idx}")
                    r_val = d_c5.number_input("失点", min_value=0, max_value=30, value=int(pitcher.get("runs_allowed", 0)), key=f"p_r_{selected_match_file}_{idx}")
                    er_val = d_c6.number_input("自責点", min_value=0, max_value=30, value=int(pitcher.get("earned_runs", 0)), key=f"p_er_{selected_match_file}_{idx}")

                    hl = st.text_input("投手寸評・配球メモ", value=str(pitcher.get("highlight", "")), key=f"p_hl_{selected_match_file}_{idx}")

                    st.write("")
                    submitted = st.form_submit_button("💾 この投手の変更を保存", use_container_width=True)
                    if submitted:
                        st.session_state.all_pitchers_data[selected_match_file][idx] = {
                            "order": idx + 1,
                            "uniform_number": u_num,
                            "player_name": p_name,
                            "role": role_val,
                            "result": res_val,
                            "innings_pitched": inn_full,
                            "innings_fraction": inn_frac,
                            "pitch_count": p_count,
                            "batters_faced": bf_val,
                            "hits_allowed": h_val,
                            "hr_allowed": pitcher.get("hr_allowed", 0),
                            "strikeouts": so_val,
                            "walks": bb_val,
                            "hit_by_pitch": hbp_val,
                            "wild_pitches": pitcher.get("wild_pitches", 0),
                            "runs_allowed": r_val,
                            "earned_runs": er_val,
                            "highlight": hl
                        }
                        st.success(f"{p_name} 投手のデータを保存しました！")
                        st.rerun()

                if st.button(f"🗑️ この投手枠（{p_name_init or '追加投手'}）を削除", key=f"del_pitcher_{selected_match_file}_{idx}"):
                    st.session_state.all_pitchers_data[selected_match_file].pop(idx)
                    st.warning(f"{p_name_init or '投手'} を削除しました。")
                    st.rerun()

        st.write("")
        if st.button("📊 全試合の投手成績を確定統合・Excelを作成する", type="primary", use_container_width=True):
            all_pitcher_compiled = []
            for m_file, p_list in st.session_state.all_pitchers_data.items():
                for p in p_list:
                    frac = p.get("innings_fraction", "0")
                    frac_num = 0.333 if frac == "1/3" else (0.666 if frac == "2/3" else 0.0)
                    inn_float = round(p.get("innings_pitched", 0) + frac_num, 3)
                    inn_disp = f"{p.get('innings_pitched', 0)}回{frac}" if frac != "0" else f"{p.get('innings_pitched', 0)}回"

                    all_pitcher_compiled.append({
                        "試合名": m_file,
                        "登板順": p.get("order", 1),
                        "背番号": p.get("uniform_number", ""),
                        "選手名": p.get("player_name", ""),
                        "役割": p.get("role", "先発"),
                        "勝敗": p.get("result", "なし"),
                        "投球回表示": inn_disp,
                        "投球回(数値)": inn_float,
                        "投球数": p.get("pitch_count", 0),
                        "対戦打者": p.get("batters_faced", 0),
                        "被安打": p.get("hits_allowed", 0),
                        "奪三振": p.get("strikeouts", 0),
                        "与四球": p.get("walks", 0),
                        "与死球": p.get("hit_by_pitch", 0),
                        "失点": p.get("runs_allowed", 0),
                        "自責点": p.get("earned_runs", 0),
                        "メモ": p.get("highlight", "")
                    })

            st.session_state["compiled_pitcher_records"] = all_pitcher_compiled
            st.success(f"🎉 全 {len(st.session_state.all_pitchers_data)} 試合分の投手成績を確定統合しました！")

    if "compiled_pitcher_records" in st.session_state:
        st.divider()
        pitcher_excel_data = create_pitching_excel(st.session_state["compiled_pitcher_records"])
        st.download_button(
            label=f"📥 全{len(st.session_state.all_pitchers_data)}試合分 投手成績サマリー付きExcelをダウンロード",
            data=pitcher_excel_data,
            file_name="チーム通算投手成績一覧.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
