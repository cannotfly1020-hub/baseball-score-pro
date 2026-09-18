import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="データ統合・通算集計",
    page_icon="📊",
    layout="wide",
)

# ----------------------------------------------------
# チームカラー UIデザイン（全画面共通仕様）
# ----------------------------------------------------
st.markdown("""
<style>
/* 1. 画面全体の背景：天然芝の深緑 */
.stApp {
    background-color: #0f1f17 !important;
    color: #f0f4f1 !important;
}

/* 2. スマホ・PC共通の余白調整 */
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
    border: 1.5px dashed #d4af37 !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* 8. 集計カード枠 */
.stat-summary-card {
    background-color: #ffffff !important;
    border: 1px solid #dcd6cd !important;
    border-left: 6px solid #991b1b !important;
    border-radius: 8px !important;
    padding: 16px 18px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35) !important;
    margin-bottom: 1.5rem !important;
}
.stat-summary-card h4,
.stat-summary-card h5,
.stat-summary-card p,
.stat-summary-card span {
    color: #111111 !important;
    font-weight: bold !important;
}

/* 9. アクションボタン */
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
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-secondary"] * {
    color: #ffffff !important;
}

/* 10. データフレーム（表）の背景引き締め */
[data-testid="stDataFrame"] {
    background-color: #ffffff !important;
    border-radius: 8px !important;
    padding: 6px !important;
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

st.subheader("📊 成績データ統合・シーズン通算集計")
st.caption("各試合でダウンロードした複数のExcel（.xlsx）をまとめ、通算成績の再計算と1冊の統合ブックを出力します。")

# ----------------------------------------------------
# ファイルアップローダー
# ----------------------------------------------------
uploaded_files = st.file_uploader(
    "統合したい過去のExcelファイルを選択（複数ファイルを一括選択・ドラッグ＆ドロップ可）",
    type=["xlsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("💡 打撃成績や投手成績でダウンロードした `.xlsx` ファイルを上の枠にまとめて投入してください。")
    st.stop()

# ----------------------------------------------------
# Excelファイル解析＆自動振り分けロジック
# ----------------------------------------------------
batting_records = []
pitching_records = []

for f in uploaded_files:
    try:
        xls = pd.ExcelFile(f)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            if df.empty:
                continue

            cols = set(df.columns)
            # 打撃成績判定
            if {"打数", "安打", "打点"}.issubset(cols) or "打率" in cols:
                if "試合名" not in df.columns:
                    df["試合名"] = f.name
                batting_records.append(df)
            # 投手成績判定
            elif {"投球数", "奪三振", "自責点"}.issubset(cols) or "防御率" in cols or "投球回(数値)" in cols:
                if "試合名" not in df.columns:
                    df["試合名"] = f.name
                pitching_records.append(df)
    except Exception as e:
        st.error(f"{f.name} の読み込み中にエラーが発生しました: {e}")

tabs = st.tabs(["⚾️ 通算打撃成績の統合", "🎯 通算投手成績の統合"])

# ====================================================
# TAB 1: 打撃成績の統合
# ====================================================
with tabs[0]:
    if batting_records:
        all_batting_df = pd.concat(batting_records, ignore_index=True)
        # 背番号・選手名でグループ化
        key_cols = [c for c in ["背番号", "選手名"] if c in all_batting_df.columns]
        if not key_cols and "選手名" in all_batting_df.columns:
            key_cols = ["選手名"]

        if key_cols:
            sum_cols = [c for c in ["打席数", "打数", "安打", "単打", "二塁打", "三塁打", "本塁打", "打点", "得点", "四球", "死球", "三振", "犠打", "犠飛", "盗塁"] if c in all_batting_df.columns]
            
            # 数値型に変換
            for col in sum_cols:
                all_batting_df[col] = pd.to_numeric(all_batting_df[col], errors='coerce').fillna(0)

            batting_summary = all_batting_df.groupby(key_cols)[sum_cols].sum().reset_index()

            # 通算指標の再計算
            if "打数" in batting_summary.columns and "安打" in batting_summary.columns:
                batting_summary["通算打率"] = batting_summary.apply(
                    lambda r: round(r["安打"] / r["打数"], 3) if r["打数"] > 0 else 0.000, axis=1
                )
            if {"打数", "四球", "死球", "安打"}.issubset(batting_summary.columns):
                batting_summary["出塁率"] = batting_summary.apply(
                    lambda r: round((r["安打"] + r["四球"] + r["死球"]) / (r["打数"] + r["四球"] + r["死球"]), 3)
                    if (r["打数"] + r["四球"] + r["死球"]) > 0 else 0.000, axis=1
                )

            st.markdown(f"#### 🏆 チーム通算打撃成績サマリー（全 {len(uploaded_files)} ファイル統合）")
            st.dataframe(batting_summary, use_container_width=True)

            # 統合Excel出力
            bat_out = io.BytesIO()
            with pd.ExcelWriter(bat_out, engine='openpyxl') as writer:
                batting_summary.to_excel(writer, sheet_name='シーズン通算打撃サマリー', index=False)
                all_batting_df.to_excel(writer, sheet_name='全試合明細データ', index=False)
                # 選手別シート
                if "選手名" in all_batting_df.columns:
                    for p_name, p_df in all_batting_df.groupby("選手名"):
                        clean_sheet_name = str(p_name)[:30]
                        p_df.to_excel(writer, sheet_name=clean_sheet_name, index=False)

            st.download_button(
                label="📥 統合通算打撃成績Excelをダウンロード",
                data=bat_out.getvalue(),
                file_name="シーズン通算_打撃成績一覧.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("打撃データ内に『選手名』列が見つかりませんでした。")
    else:
        st.info("アップロードされたファイルに打撃成績データが見つかりませんでした。")

# ====================================================
# TAB 2: 投手成績の統合
# ====================================================
with tabs[1]:
    if pitching_records:
        all_pitch_df = pd.concat(pitching_records, ignore_index=True)
        key_cols = [c for c in ["背番号", "選手名"] if c in all_pitch_df.columns]
        if not key_cols and "選手名" in all_pitch_df.columns:
            key_cols = ["選手名"]

        if key_cols:
            num_cols = [c for c in ["投球回(数値)", "投球数", "対戦打者", "被安打", "奪三振", "与四球", "与死球", "失点", "自責点"] if c in all_pitch_df.columns]
            for col in num_cols:
                all_pitch_df[col] = pd.to_numeric(all_pitch_df[col], errors='coerce').fillna(0)

            pitch_summary = all_pitch_df.groupby(key_cols).agg(
                登板試合数=("試合名", "count"),
                通算投球回=("投球回(数値)", "sum") if "投球回(数値)" in num_cols else ("投球数", "count"),
                合計球数=("投球数", "sum") if "投球数" in num_cols else ("試合名", "count"),
                奪三振=("奪三振", "sum") if "奪三振" in num_cols else ("試合名", "count"),
                与四死球=("与四球", "sum") if "与四球" in num_cols else ("試合名", "count"),
                被安打=("被安打", "sum") if "被安打" in num_cols else ("試合名", "count"),
                失点=("失点", "sum") if "失点" in num_cols else ("試合名", "count"),
                自責点=("自責点", "sum") if "自責点" in num_cols else ("試合名", "count"),
                勝利=("勝敗", lambda x: (x == "勝").sum()) if "勝敗" in all_pitch_df.columns else ("試合名", lambda x: 0),
                敗戦=("勝敗", lambda x: (x == "敗").sum()) if "勝敗" in all_pitch_df.columns else ("試合名", lambda x: 0),
                セーブ=("勝敗", lambda x: (x == "Ｓ").sum()) if "勝敗" in all_pitch_df.columns else ("試合名", lambda x: 0),
            ).reset_index()

            # 通算防御率再計算（学童野球7回換算）
            if "通算投球回" in pitch_summary.columns and "自責点" in pitch_summary.columns:
                pitch_summary["通算防御率"] = pitch_summary.apply(
                    lambda r: round((r["自責点"] * 7) / r["通算投球回"], 2) if r["通算投球回"] > 0 else 0.00, axis=1
                )

            st.markdown(f"#### 🏆 チーム通算投手成績サマリー（全 {len(uploaded_files)} ファイル統合）")
            st.dataframe(pitch_summary, use_container_width=True)

            # 統合Excel出力
            pitch_out = io.BytesIO()
            with pd.ExcelWriter(pitch_out, engine='openpyxl') as writer:
                pitch_summary.to_excel(writer, sheet_name='シーズン通算投手サマリー', index=False)
                all_pitch_df.to_excel(writer, sheet_name='全試合投手明細データ', index=False)
                if "選手名" in all_pitch_df.columns:
                    for p_name, p_df in all_pitch_df.groupby("選手名"):
                        clean_sheet_name = str(p_name)[:30]
                        p_df.to_excel(writer, sheet_name=clean_sheet_name, index=False)

            st.download_button(
                label="📥 統合通算投手成績Excelをダウンロード",
                data=pitch_out.getvalue(),
                file_name="シーズン通算_投手成績一覧.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("投手データ内に『選手名』列が見つかりませんでした。")
    else:
        st.info("アップロードされたファイルに投手成績データが見つかりませんでした。")
