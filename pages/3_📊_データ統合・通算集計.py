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

st.markdown("""
<style>
    /* スタジアム風グラデーション背景 */
    .stApp {
        background: radial-gradient(circle at 50% 10%, rgba(26, 56, 38, 0.55) 0%, transparent 65%),
                    linear-gradient(165deg, #102418 0%, #0a1710 40%, #050d09 100%);
        color: #f1f5f3;
    }
    /* メトリクス表示カード */
    .metric-card {
        background: #112217;
        border: 1px solid #1f422e;
        border-left: 5px solid #d4af37;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .metric-card h4 {
        color: #d4af37;
        margin: 0 0 6px 0;
        font-size: 0.92rem;
    }
    .metric-card p {
        color: #e2e8f0;
        margin: 0;
        font-size: 1.4rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 データ統合・チーム通算集計")
st.markdown("保存された試合ごとのExcelファイル（.xlsx）を取り込み、選手ごとに名寄せして通算打撃成績を集計します。")

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
    "試合記録Excelファイル（.xlsx）をアップロードしてください（複数ファイル選択可）",
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

    st.success(f"計 {len(uploaded_files)} ファイルから {len(raw_df)} 件の打撃レコードを正常に統合しました（まとめシートの重複を自動除外済）。")

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

    # サマリーメトリクスカード表示
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><h4>登録選手数</h4><p>{len(summary_df)} 名</p></div>', unsafe_allow_html=True)
    with m2:
        total_hits = summary_df["安打"].sum()
        st.markdown(f'<div class="metric-card"><h4>チーム総安打数</h4><p>{total_hits} 本</p></div>', unsafe_allow_html=True)
    with m3:
        total_rbi = summary_df["打点"].sum()
        st.markdown(f'<div class="metric-card"><h4>チーム総打点</h4><p>{total_rbi} 点</p></div>', unsafe_allow_html=True)
    with m4:
        total_hr = summary_df["本塁打"].sum()
        st.markdown(f'<div class="metric-card"><h4>総本塁打数</h4><p>{total_hr} 本</p></div>', unsafe_allow_html=True)

    st.subheader("📋 選手別通算打撃成績一覧（1人1行 名寄せ集計済）")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # 通算Excelファイルのダウンロード
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="通算打撃成績")
    
    st.download_button(
        label="📥 通算成績をExcel形式でダウンロード (.xlsx)",
        data=buffer.getvalue(),
        file_name="チーム通算打撃成績_名寄せ集計済.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

else:
    st.info("集計対象のExcelファイルをドラッグ＆ドロップしてください。重複シート（通算・選手別等）を自動除外し、選手名で統合集計します。")
