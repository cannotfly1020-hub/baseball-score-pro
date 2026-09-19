import io
import os
import pandas as pd
import openpyxl
import streamlit as st

st.set_page_config(
    page_title="データ統合・チーム通算集計",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# チームカラー UIデザイン（打撃成績入力画面と完全統一）
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

/* 3. 見出し・タイトルの装飾 */
h1, h2, h3, h4 {
    color: #ffffff !important;
}

/* 4. ファイルアップローダー（金枠ダッシュ・ダークグリーン背景） */
[data-testid="stFileUploader"] {
    background-color: #172d22 !important;
    border: 1.5px dashed #d4af37 !important;
    border-radius: 10px !important;
    padding: 12px !important;
}
[data-testid="stFileUploader"] label p,
[data-testid="stFileUploader"] span {
    color: #f0f4f1 !important;
    font-weight: bold !important;
}

/* 5. アクションボタン・ダウンロードボタン（クリムゾンレッド ＋ 金枠 ＋ 白文字） */
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
.stDownloadButton button {
    background-color: #991b1b !important;
    color: #ffffff !important;
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    font-size: 0.95rem !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-secondary"] *,
.stDownloadButton button * {
    color: #ffffff !important;
}

/* 6. サマリーメトリクスカード（スコア用紙白 ＋ 赤金ストライプ枠） */
.metric-card {
    background-color: #ffffff !important;
    border: 1px solid #dcd6cd !important;
    border-left: 6px solid #991b1b !important;
    border-radius: 8px !important;
    padding: 12px 14px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}
.metric-card h4 {
    color: #111111 !important;
    margin: 0 0 4px 0 !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
}
.metric-card p {
    color: #991b1b !important;
    margin: 0 !important;
    font-size: 1.5rem !important;
    font-weight: 800 !important;
}

/* 7. データフレーム（表）の背景と境界線 */
[data-testid="stDataFrame"] {
    background-color: #112217 !important;
    border: 1px solid #2d5a45 !important;
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

st.subheader("📊 データ統合・チーム通算集計")
st.caption("保存された試合ごとのExcelファイル（.xlsx）を取り込み、選手ごとに名寄せして通算打撃成績を集計します。")

def is_valid_game_sheet(sheet_name: str) -> bool:
    """
    試合ごとの個別打撃記録シートのみを集計対象とする判定。
    「通算」「集計」「選手別」「個人」などのまとめシートを自動検知して除外し、二重カウントを防ぐ。
    """
    exclude_keywords = ["通算", "集計", "まとめ", "個人", "選手別", "テンプレート", "設定", "マスタ"]
    for kw in exclude_keywords:
        if kw in sheet_name:
            return False
    return True

uploaded_files = st.file_uploader(
    "試合記録Excelファイル（.xlsx）を選択してください（複数ファイル選択可）",
    type=["xlsx"],
    accept_multiple_files=True
)

all_records = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            for sheet in excel_data.sheet_names:
                # 重複防止判定：まとめシートや選手別シートはスキップ
                if not is_valid_game_sheet(sheet):
                    continue

                df_sheet = pd.read_excel(excel_data, sheet_name=sheet)

                # 必須カラム「選手名」が存在しないシートはスキップ
                if "選手名" not in df_sheet.columns:
                    continue

                # 欠損行・合計行・チーム行の除外
                df_sheet = df_sheet.dropna(subset=["選手名"])
                df_sheet = df_sheet[~df_sheet["選手名"].astype(str).str.contains("合計|チーム|計", na=False)]

                # 出典シート情報の保持
                df_sheet["試合・シート名"] = f"{uploaded_file.name} - {sheet}"
                all_records.append(df_sheet)

        except Exception as e:
            st.error(f"ファイル読み込みエラー ({uploaded_file.name}): {e}")

if all_records:
    raw_df = pd.concat(all_records, ignore_index=True)

    # 選手名の前後の空白・全角スペースを除去し、同一人物の名寄せ精度を担保
    raw_df["選手名"] = raw_df["選手名"].astype(str).str.strip().str.replace("　", " ")

    # 数値カラムの安全な数値変換（欠損値は0で補正）
    stat_cols = ["打数", "安打", "単打", "二塁打", "三塁打", "本塁打", "打点", "得点", "四球", "死球", "三振", "犠打", "犠飛", "盗塁", "失策"]
    for col in stat_cols:
        if col in raw_df.columns:
            raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce").fillna(0).astype(int)
        else:
            raw_df[col] = 0

    st.success(f"🎉 計 {len(uploaded_files)} ファイルから {len(raw_df)} 件の打撃レコードを統合しました（まとめシートの重複を自動除外済）。")

    # 各選手の最新の背番号を取得（最後の行の記録を採用）
    latest_numbers = raw_df.groupby("選手名")["背番号"].last().fillna("-").astype(str)

    # 選手名を主キーとして合算集計（1人1行）
    agg_dict = {col: "sum" for col in stat_cols}
    agg_dict["試合・シート名"] = "count"

    summary_df = raw_df.groupby("選手名", as_index=False).agg(agg_dict)
    summary_df.rename(columns={"試合・シート名": "出場機会数"}, inplace=True)

    # 代表背番号を結合
    summary_df["背番号"] = summary_df["選手名"].map(latest_numbers)

    # 打席数 = 打数 + 四球 + 死球 + 犠打 + 犠飛
    summary_df["打席数"] = summary_df["打数"] + summary_df["四球"] + summary_df["死球"] + summary_df["犠打"] + summary_df["犠飛"]

    # 打率 = 安打 / 打数
    summary_df["打率"] = summary_df.apply(
        lambda r: f"{r['安打'] / r['打数']:.3f}" if r["打数"] > 0 else ".000", axis=1
    )

    # 出塁率 = (安打 + 四球 + 死球) / (打数 + 四球 + 死球 + 犠飛)
    summary_df["出塁率"] = summary_df.apply(
        lambda r: f"{(r['安打'] + r['四球'] + r['死球']) / (r['打数'] + r['四球'] + r['死球'] + r['犠飛']):.3f}"
        if (r["打数"] + r["四球"] + r["死球"] + r["犠飛"]) > 0 else ".000", axis=1
    )

    # 長打率 = (単打 + 二塁打*2 + 三塁打*3 + 本塁打*4) / 打数
    summary_df["長打率"] = summary_df.apply(
        lambda r: f"{(r['単打'] + r['二塁打']*2 + r['三塁打']*3 + r['本塁打']*4) / r['打数']:.3f}"
        if r["打数"] > 0 else ".000", axis=1
    )

    # OPS = 出塁率 + 長打率
    summary_df["OPS"] = summary_df.apply(
        lambda r: f"{float(r['出塁率']) + float(r['長打率']):.3f}", axis=1
    )

    # カラムの並び順整理（背番号・選手名を先頭へ配置）
    display_cols = [
        "背番号", "選手名", "打率", "出場機会数",
        "打席数", "打数", "安打", "二塁打", "三塁打", "本塁打",
        "打点", "得点", "四球", "死球", "三振", "犠打", "犠飛", "盗塁", "出塁率", "長打率", "OPS"
    ]
    display_cols = [c for c in display_cols if c in summary_df.columns]
    summary_df = summary_df[display_cols].sort_values(by=["安打", "打率"], ascending=False).reset_index(drop=True)

    # サマリーメトリクス表示（Streamlit標準機能で100%確実に文字を表示）
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("登録選手数", f"{len(summary_df)} 名")
    m2.metric("チーム総安打数", f"{summary_df['安打'].sum()} 本")
    m3.metric("チーム総打点", f"{summary_df['打点'].sum()} 点")
    m4.metric("総本塁打数", f"{summary_df['本塁打'].sum()} 本")

    st.markdown("#### 📋 選手別通算打撃成績一覧（1人1行 名寄せ集計済）")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.divider()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="通算打撃成績")
    
    st.download_button(
        label="📥 チーム通算打撃成績Excelをダウンロード (.xlsx)",
        data=buffer.getvalue(),
        file_name="チーム通算打撃成績_名寄せ集計済.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

else:
    st.info("集計対象のExcelファイルをドラッグ＆ドロップしてください。重複シート（通算・選手別等）を自動除外し、選手名で統合集計します。")
