import io
import json
import base64
from datetime import datetime
from google import genai
from google.genai import types
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# 独立させたモジュールから読み込み
from prompts.batting_prompts import ROSTER_PROMPT, DETAILS_PROMPT
from utils.batting_utils import enhance_sharpness, calculate_stats_from_grid, create_excel_from_compiled, RESULT_OPTIONS

st.set_page_config(
    page_title="打撃成績解析＆エディタ",
    page_icon="⚾️",
    layout="wide",
)

# ----------------------------------------------------
# チームカラー UIデザイン（ホーム画面と完全統一）
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

/* カード内の見出し・全ラベルを真っ黒＆くっきり太字に強制 */
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

/* 数値入力（打点・盗塁）の「＋」「−」ステップボタンを上品なグレーに */
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

/* 10. 【最重要】各回の打席プルダウン（赤潰れを解消し、白地・くっきり黒文字へ） */
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
div[data-testid="stForm"] div[data-baseweb="select"] svg {
    fill: #2d5a45 !important;
}
/* スマホでのキーボード立ち上がり防止 */
div[data-baseweb="select"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
    user-select: none !important;
}

/* 11. イニング枠ヘッダー（◇ ダイヤモンド） */
.inning-header {
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
.diamond-icon {
    color: #ffd700 !important;
    margin-right: 3px;
    font-size: 0.9rem;
}

/* 12. アクションボタン（変更を保存・AI解析・Excel作成）のみクリムゾンレッド ＋ 金枠 */
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

    /* 画面背景側の一般テキスト（カード外のみ適用） */
    .stApp > div p, .stApp > div span {
        color: #f0f4f1 !important;
    }

    hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border-color: #2d5a45 !important;
    }

    /* ---------------------------------------------------
       PCカード内の文字色を強制的に黒へ固定（白飛び解消）
       --------------------------------------------------- */
    div[data-testid="stForm"] h5,
    div[data-testid="stForm"] h5 *,
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] p *,
    div[data-testid="stForm"] span,
    div[data-testid="stForm"] strong {
        color: #111111 !important;
    }

    /* ---------------------------------------------------
       PCプルダウンの余白圧縮＆矢印サイズ最適化
       --------------------------------------------------- */
    /* セレクトボックス内部全体の左右余白を限界までカット */
    div[data-testid="stForm"] div[data-baseweb="select"] > div {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }

    /* 文字コンテナ：はみ出しを防止し適正サイズで全文表示 */
    div[data-testid="stForm"] div[data-baseweb="select"] div[aria-hidden="true"],
    div[data-testid="stForm"] div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stForm"] div[data-baseweb="select"] span {
        font-size: 0.68rem !important;
        letter-spacing: -0.5px !important;
        white-space: nowrap !important;
    }

   /* 右端の下矢印エリア（ラッパーコンテナごと）を完全に消去 */
    div[data-testid="stForm"] div[data-baseweb="select"] [aria-hidden="true"] {
        display: none !important;
    }
    div[data-testid="stForm"] div[data-baseweb="select"] svg,
    div[data-testid="stForm"] div[data-baseweb="select"] span[data-baseweb="icon"] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    }

    /* ---------------------------------------------------
       サイドバー全体の背景・枠・文字色
       --------------------------------------------------- */
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

# セッション状態の初期化
if "all_matches_data" not in st.session_state:
    st.session_state.all_matches_data = {}
if "match_images_b64" not in st.session_state:
    st.session_state.match_images_b64 = {}

# APIキー設定
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("管理者APIキー (Gemini)", type="password")

client = genai.Client(api_key=api_key) if api_key else None

st.subheader("⚾️ スコア照合・打席盤面エディタ")
st.caption("高精細カラー解析により、手書き文字および赤ペン結線を走査・判定します。")

# ----------------------------------------------------
# バックアップ読み込み（打撃アプリの完全復元ロジック）
# ----------------------------------------------------
with st.expander("📂 前回の作業バックアップ（JSON）を読み込んで再開する", expanded=False):
    backup_file = st.file_uploader(
        "保存したバックアップJSONファイルを選択",
        type=["json"],
        key="backup_uploader_direct"
    )
    if backup_file is not None:
        if st.button("このバックアップから作業を完全復元する", type="secondary", use_container_width=True):
            try:
                loaded_data = json.loads(backup_file.getvalue().decode("utf-8"))
                if "all_matches_data" in loaded_data:
                    st.session_state.all_matches_data = loaded_data["all_matches_data"]
                    st.session_state.match_images_b64 = loaded_data.get("match_images_b64", {})
                    st.success(f"🎉 全 {len(st.session_state.all_matches_data)} 試合分の編集データを完全に復元しました！")
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
    "新規スコアブック写真を選択（複数ファイル選択可）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button(f"AIで全{len(uploaded_files)}試合を高精度一括解析する", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        new_all_matches = {}
        new_images_b64 = {}

        for idx, f in enumerate(uploaded_files):
            f_name = f.name
            status_text.text(f"【{idx+1}/{len(uploaded_files)}】{f_name} の高解像度鮮鋭化＆選手名簿を確定中...")
            raw_bytes = f.read()
            new_images_b64[f_name] = base64.b64encode(raw_bytes).decode()
            
            pil_img = Image.open(io.BytesIO(raw_bytes))
            highres_bytes = enhance_sharpness(pil_img)

            try:
                # Step 1: 選手名簿の確定
                res_roster = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_bytes(data=highres_bytes, mime_type="image/jpeg"),
                        "スコアブック左側の打順・背番号・選手名（先発・交代・代打二段書き含む）を漏れなく抽出してください。"
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=ROSTER_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                roster_data = res_roster.text

                # Step 2: 打席判定
                status_text.text(f"【{idx+1}/{len(uploaded_files)}】{f_name} の全イニング打席を精査中...")
                res_details = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_bytes(data=highres_bytes, mime_type="image/jpeg"),
                        f"確定選手名簿:\n{roster_data}\n\n上記選手枠に基づき、スコアブックの1回〜7回の全打席詳細、打点、盗塁を判定してください。"
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=DETAILS_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                parsed = json.loads(res_details.text)
                new_all_matches[f_name] = parsed

            except Exception as e:
                st.error(f"{f_name} の解析エラー: {e}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.empty()
        if new_all_matches:
            st.session_state.all_matches_data = new_all_matches
            st.session_state.match_images_b64 = new_images_b64
            st.success(f"🎉 全 {len(new_all_matches)} 試合分の解析が完了しました！")

# ----------------------------------------------------
# データが存在する場合の編集エディタ & バックアップ保存
# ----------------------------------------------------
if st.session_state.all_matches_data:
    st.divider()

    # バックアップダウンロード
    current_backup_payload = {
        "all_matches_data": st.session_state.all_matches_data,
        "match_images_b64": st.session_state.match_images_b64,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    json_string = json.dumps(current_backup_payload, ensure_ascii=False, indent=2)

    st.download_button(
        label="💾 現在の作業状態をバックアップ保存 (JSONダウンロード)",
        data=json_string,
        file_name=f"学童野球スコア_途中作業データ_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

    match_files = list(st.session_state.all_matches_data.keys())
    
    top_c1, top_c2 = st.columns([2, 1])
    selected_match_file = top_c1.selectbox("📁 確認・編集する試合を選択", match_files)
    is_mobile_sticky = top_c2.checkbox("📱 スマホ表示（画像を上部に固定）", value=False)

    current_players = st.session_state.all_matches_data.get(selected_match_file, [])
    current_b64 = st.session_state.match_images_b64.get(selected_match_file, "")

    add_col1, add_col2 = st.columns([1, 3])
    with add_col1:
        if st.button("➕ この試合に選手を手動追加"):
            new_player_template = {
                "batting_order": len(current_players) + 1,
                "uniform_number": "",
                "player_name": f"追加選手{len(current_players) + 1}",
                "is_substitute": True,
                "rbi": 0,
                "stolen_bases": 0,
                "innings": {"1": "なし", "2": "なし", "3": "なし", "4": "なし", "5": "なし", "6": "なし", "7": "なし"},
                "highlight": ""
            }
            st.session_state.all_matches_data[selected_match_file].append(new_player_template)
            st.rerun()

    col_img, col_grid = st.columns([0.9, 1.5])

    with col_img:
        st.markdown(f"#### 📷 原本画像: `{selected_match_file}`")
        zoom_val = st.slider("🔍 拡大率", min_value=100, max_value=350, value=150, step=25, format="%d%%")
        
        box_height = 320 if is_mobile_sticky else 620
        sticky_class = "sticky-mobile-viewer" if is_mobile_sticky else ""

        viewer_html = f"""
        <div class="{sticky_class}" style="width:100%; height:{box_height}px; overflow:auto; border:2px solid #555; border-radius:8px; background-color:#222; text-align:center;">
            <img src="data:image/jpeg;base64,{current_b64}" style="width:{zoom_val}%; max-width:none; transition:width 0.15s ease-in-out; cursor:grab;" />
        </div>
        """
        components.html(viewer_html, height=box_height + 20)

    with col_grid:
        st.markdown("#### 🎯 打席盤面エディタ")
        st.caption("タブを指で横にスワイプして選手を選択し、修正後は「保存」を押してください。")

        tab_labels = []
        for idx, player in enumerate(current_players):
            u_num = str(player.get("uniform_number", "")).strip()
            num_str = f"#{u_num} " if u_num else ""
            p_name = str(player.get("player_name", "選手")).strip()
            sub_tag = "(代)" if player.get("is_substitute") else ""
            tab_labels.append(f"{num_str}{p_name}{sub_tag}")

        player_tabs = st.tabs(tab_labels)

        for idx, (p_tab, player) in enumerate(zip(player_tabs, current_players)):
            with p_tab:
                is_sub = player.get("is_substitute", False)
                order_val = player.get("batting_order", idx + 1)
                u_num_init = str(player.get("uniform_number", "")).strip()
                p_name_init = str(player.get("player_name", "")).strip()

                with st.form(key=f"form_player_{selected_match_file}_{idx}"):
                    st.markdown(f"##### **【{order_val}番】 #{u_num_init or '-'} {p_name_init} {'（途中交代・代打）' if is_sub else '（先発）'}**")

                    p_cols = st.columns([1, 2, 3])
                    u_num = p_cols[0].text_input("背番号", value=u_num_init, key=f"{selected_match_file}_num_{idx}")
                    p_name = p_cols[1].text_input("選手名（漢字）", value=p_name_init, key=f"{selected_match_file}_name_{idx}")
                    hl = p_cols[2].text_input("ハイライトメモ", value=str(player.get("highlight", "")), key=f"{selected_match_file}_hl_{idx}")

                    stat_c1, stat_c2 = st.columns(2)
                    rbi_val = stat_c1.number_input("打点 (RBI)", min_value=0, max_value=20, value=int(player.get("rbi", 0)), step=1, key=f"{selected_match_file}_rbi_{idx}")
                    sb_val = stat_c2.number_input("盗塁数 (SB)", min_value=0, max_value=20, value=int(player.get("stolen_bases", 0)), step=1, key=f"{selected_match_file}_sb_{idx}")

                    st.markdown("**各回の打席結果（◇ダイヤモンド）**")
                    inn_cols = st.columns(7)
                    new_innings = {}
                    for i_idx, inn_str in enumerate(["1", "2", "3", "4", "5", "6", "7"]):
                        with inn_cols[i_idx]:
                            st.markdown(f"<div class='inning-header'><span class='diamond-icon'>◇</span>{inn_str}回</div>", unsafe_allow_html=True)
                            cur_val = player.get("innings", {}).get(inn_str, "なし")
                            default_idx = RESULT_OPTIONS.index(cur_val) if cur_val in RESULT_OPTIONS else 0
                            sel = st.selectbox(
                                f"{inn_str}回",
                                RESULT_OPTIONS,
                                index=default_idx,
                                key=f"{selected_match_file}_inn_{idx}_{inn_str}",
                                label_visibility="collapsed"
                            )
                            new_innings[inn_str] = sel

                    st.write("")
                    submitted = st.form_submit_button("💾 この選手の変更を保存", use_container_width=True)
                    if submitted:
                        st.session_state.all_matches_data[selected_match_file][idx] = {
                            "match_date": player.get("match_date", "-"),
                            "opponent": player.get("opponent", "-"),
                            "batting_order": order_val,
                            "uniform_number": u_num,
                            "player_name": p_name,
                            "is_substitute": is_sub,
                            "rbi": rbi_val,
                            "stolen_bases": sb_val,
                            "innings": new_innings,
                            "highlight": hl
                        }
                        st.success(f"{p_name} 選手のデータを保存しました！")
                        st.rerun()

                # 誤って追加した選手枠の削除ボタン
                if st.button(f"🗑️ この選手枠（{p_name_init or '追加選手'}）を削除", key=f"del_btn_{selected_match_file}_{idx}"):
                    st.session_state.all_matches_data[selected_match_file].pop(idx)
                    st.warning(f"{p_name_init or '選手'} を削除しました。")
                    st.rerun()

        st.write("")
        if st.button("📊 全試合の成績を統合確定・Excelを作成する", type="primary", use_container_width=True):
            all_compiled = []
            for m_file, p_list in st.session_state.all_matches_data.items():
                compiled_single = calculate_stats_from_grid(p_list, match_file_name=m_file)
                all_compiled.extend(compiled_single)

            st.session_state["compiled_records"] = all_compiled
            st.success(f"🎉 全 {len(st.session_state.all_matches_data)} 試合分の成績を確定統合しました！")

    if "compiled_records" in st.session_state:
        st.divider()
        excel_data = create_excel_from_compiled(st.session_state["compiled_records"])
        st.download_button(
            label=f"📥 全{len(st.session_state.all_matches_data)}試合分 選手名別シート付きExcelをダウンロード",
            data=excel_data,
            file_name="チーム通算打撃成績一覧.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
