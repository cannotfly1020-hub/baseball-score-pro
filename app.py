import io
import json
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="学童野球スコア統合名鑑＆アワード",
    page_icon="⚾️",
    layout="wide",
)

st.markdown("""
<style>
/* 1. 画面全体の背景：天然芝の深緑 */
.stApp {
    background-color: #0f1f17 !important;
    color: #f0f4f1 !important;
}

/* 2. スマホ上部スペース（スマホ時は既存数値を完全維持） */
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

/* 4. メトリック数値：金色 */
div[data-testid="stMetricValue"] {
    color: #ffd700 !important;
    font-weight: bold !important;
}

/* 5. ファイルアップローダー */
[data-testid="stFileUploader"] {
    background-color: #172d22 !important;
    border: 1px dashed #d4af37 !important;
    border-radius: 10px !important;
    padding: 10px !important;
}

/* 6. ボタン：クリムゾンレッド ＋ 金枠 ＋ 白文字 */
button[kind="primary"], button[kind="secondary"] {
    background-color: #991b1b !important;
    color: #ffffff !important;
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
}
button * {
    color: #ffffff !important;
}

/* ===================================================
   PCモニター表示専用（横幅768px以上）の最適化
   =================================================== */
@media (min-width: 768px) {
    /* PCでの無駄な上下余白を圧縮し、最大幅を適正化 */
    .block-container {
        padding-top: 2.0rem !important;
        padding-bottom: 2.0rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1400px !important;
    }

    /* PCモニターで沈んで見えにくかった説明文・案内文のコントラストを大幅強化 */
    div[data-testid="stCaptionContainer"] p {
        color: #e0ece5 !important;
        font-size: 1.0rem !important;
        font-weight: 500 !important;
    }

    /* 各種テキスト・小見出しの白文字コントラスト強化 */
    p, span, label {
        color: #f0f4f1 !important;
    }

    /* メトリックタイトルのコントラスト強化 */
    div[data-testid="stMetricLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* 区切り線（divider）の余白を適正に縮小 */
    hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border-color: #2d5a45 !important;
    }
   @media (min-width: 768px) {
    /* 1. サイドバー全体の横幅を指定（例: 260px に調整） */
    section[data-testid="stSidebar"] {
        width: 180px !important;
        min-width: 260px !important;
    }

    /* 2. /* 1. サイドバー全体の背景：深みのあるクリムゾンレッド */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background-color: #801212 !important;
    }
　　
   /* 3. サイドバー右端：金色の縦ライン */
    section[data-testid="stSidebar"] {
        border-right: 3px solid #d4af37 !important;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.5) !important;
    }
   
    /* 4. メニュー文字色：赤背景で見やすい純白＋太字 */
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* 5. 選択中のメニュー項目の文字色（ゴールド） */
    section[data-testid="stSidebar"] [aria-selected="true"] span,
    section[data-testid="stSidebar"] [aria-selected="true"] p {
        color: #ffd700 !important;
        font-weight: bold !important;
    }
　}
}
</style>
""", unsafe_allow_html=True)

def create_integrated_excel(compiled_batting: list, compiled_pitching: list) -> bytes:
    """打撃・投手の統合成績および選手別個人シート付きExcel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if compiled_batting:
            pd.DataFrame(compiled_batting).to_excel(writer, sheet_name="全打席成績一覧", index=False)
        if compiled_pitching:
            pd.DataFrame(compiled_pitching).to_excel(writer, sheet_name="全投手成績一覧", index=False)

        df_bat = pd.DataFrame(compiled_batting) if compiled_batting else pd.DataFrame()
        all_players = set()
        if not df_bat.empty:
            all_players.update(df_bat["player_name"].dropna().unique())

        for p in all_players:
            p_str = str(p).strip()
            if not p_str:
                continue
            sheet_title = p_str[:28].replace("/", "_").replace("\\", "_")
            p_bat = df_bat[df_bat["player_name"] == p]
            p_bat.to_excel(writer, sheet_name=sheet_title, index=False)
            
    return output.getvalue()

if "all_matches_data" not in st.session_state:
    st.session_state.all_matches_data = {}
if "all_pitchers_data" not in st.session_state:
    st.session_state.all_pitchers_data = {}

st.title("⚾️ 学童野球 スコア統合集計＆デジタル名鑑")
st.caption("左側のサイドバーメニューから「1_⚾️_打撃成績入力」または「2_🛡️_投手成績入力」を選んで解析・編集を行ってください。")

with st.expander("📂 作業バックアップ（JSON）を読み込む / 保存する", expanded=False):
    up_backup = st.file_uploader("保存済みバックアップJSONファイルを選択", type=["json"])
    if up_backup:
        if st.button("このバックアップから全データを完全復元", use_container_width=True):
            loaded = json.loads(up_backup.getvalue().decode("utf-8"))
            st.session_state.all_matches_data = loaded.get("all_matches_data", {})
            st.session_state.all_pitchers_data = loaded.get("all_pitchers_data", {})
            st.success("🎉 打撃＆投手データを完全復元しました！")
            st.rerun()

    if st.session_state.all_matches_data or st.session_state.all_pitchers_data:
        backup_dict = {
            "all_matches_data": st.session_state.all_matches_data,
            "all_pitchers_data": st.session_state.all_pitchers_data,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.download_button(
            "💾 現在の全作業状態をバックアップ保存 (JSONダウンロード)",
            data=json.dumps(backup_dict, ensure_ascii=False, indent=2),
            file_name=f"学童野球_打撃投手バックアップ_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

st.divider()

compiled_bat = st.session_state.get("compiled_records", [])
compiled_pit = st.session_state.get("compiled_pitchers", [])

if not compiled_bat and not compiled_pit:
    st.info("👈 まず左側のメニューから各成績入力ページを開き、スコアの確定を行ってください。")
else:
    df_bat = pd.DataFrame(compiled_bat) if compiled_bat else pd.DataFrame()
    df_pit = pd.DataFrame(compiled_pit) if compiled_pit else pd.DataFrame()

    st.subheader("🎖️ チームタイトル・アワード（打撃部門）")
    if not df_bat.empty:
        df_bat["total_hits"] = df_bat["hits"] + df_bat["doubles"] + df_bat["triples"] + df_bat["homeruns"]
        c1, c2, c3, c4 = st.columns(4)
        th_l = df_bat.groupby("player_name")["total_hits"].sum().sort_values(ascending=False)
        if not th_l.empty and th_l.iloc[0] > 0:
            c1.metric("最多安打賞", f"{th_l.index[0]} 選手", f"{int(th_l.iloc[0])} 本")
        hr_l = df_bat.groupby("player_name")["homeruns"].sum().sort_values(ascending=False)
        if not hr_l.empty and hr_l.iloc[0] > 0:
            c2.metric("スラッガー賞(本塁打)", f"{hr_l.index[0]} 選手", f"{int(hr_l.iloc[0])} 本")
        rbi_l = df_bat.groupby("player_name")["rbi"].sum().sort_values(ascending=False)
        if not rbi_l.empty and rbi_l.iloc[0] > 0:
            c3.metric("クラッチヒッター賞(打点)", f"{rbi_l.index[0]} 選手", f"{int(rbi_l.iloc[0])} 打点")
        sb_l = df_bat.groupby("player_name")["stolen_bases"].sum().sort_values(ascending=False)
        if not sb_l.empty and sb_l.iloc[0] > 0:
            c4.metric("スピードスター賞(盗塁)", f"{sb_l.index[0]} 選手", f"{int(sb_l.iloc[0])} 個")

    if not df_pit.empty:
        st.divider()
        st.subheader("🎖️ チームタイトル・アワード（投手部門・学童6回基準）")
        pc1, pc2, pc3 = st.columns(3)
        wins_df = df_pit[df_pit["decision"].str.contains("勝利", na=False)]
        if not wins_df.empty:
            w_l = wins_df.groupby("player_name").size().sort_values(ascending=False)
            pc1.metric("最多勝投手", f"{w_l.index[0]} 投手", f"{int(w_l.iloc[0])} 勝")
        so_l = df_pit.groupby("player_name")["strikeouts"].sum().sort_values(ascending=False)
        if not so_l.empty and so_l.iloc[0] > 0:
            pc2.metric("奪三振王", f"{so_l.index[0]} 投手", f"{int(so_l.iloc[0])} 個")
        
        valid_era = df_pit[df_pit["actual_ip"] > 0]
        if not valid_era.empty:
            tot_er = valid_era.groupby("player_name")["earned_runs"].sum()
            tot_ip = valid_era.groupby("player_name")["actual_ip"].sum()
            era_calc = (tot_er * 6.0 / tot_ip).sort_values()
            if not era_calc.empty:
                pc3.metric("最優秀防御率", f"{era_calc.index[0]} 投手", f"{era_calc.iloc[0]:.2f}")

    st.divider()
    st.subheader("⚾️ デジタル選手名鑑（打撃＆投手通算）")
    all_p_names = sorted(list(set(df_bat["player_name"].dropna().tolist() + df_pit["player_name"].dropna().tolist())))
    sel_p = st.selectbox("選手を選択してください（名前で通算集計）", all_p_names)

    p_b = df_bat[df_bat["player_name"] == sel_p] if not df_bat.empty else pd.DataFrame()
    p_p = df_pit[df_pit["player_name"] == sel_p] if not df_pit.empty else pd.DataFrame()

    if not p_b.empty:
        ab = p_b["at_bats"].sum()
        h = p_b["total_hits"].sum()
        avg = (h / ab) if ab > 0 else 0.0
        st.markdown(f"#### **{sel_p}** 選手の確定通算打撃成績")
        bc1, bc2, bc3, bc4, bc5 = st.columns(5)
        bc1.metric("通算打率", f".{int(avg * 1000):03d}" if avg > 0 else ".000")
        bc2.metric("安打", f"{int(h)} 本")
        bc3.metric("本塁打", f"{int(p_b['homeruns'].sum())} 本")
        bc4.metric("打点", f"{int(p_b['rbi'].sum())} 点")
        bc5.metric("盗塁", f"{int(p_b['stolen_bases'].sum())} 個")

    if not p_p.empty and p_p["actual_ip"].sum() > 0:
        tot_ip_act = p_p["actual_ip"].sum()
        tot_er = p_p["earned_runs"].sum()
        era = (tot_er * 6.0 / tot_ip_act) if tot_ip_act > 0 else 0.0
        whip = ((p_p["hits_allowed"].sum() + p_p["walks_allowed"].sum() + p_p["hit_by_pitch"].sum()) / tot_ip_act) if tot_ip_act > 0 else 0.0
        
        st.markdown(f"#### **{sel_p}** 選手の確定通算投球成績（6回基準）")
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("投球回", f"{tot_ip_act:.1f} 回")
        tc2.metric("防御率 (ERA)", f"{era:.2f}")
        tc3.metric("WHIP", f"{whip:.2f}")
        tc4.metric("奪三振", f"{int(p_p['strikeouts'].sum())} 個")

    st.divider()
    excel_bin = create_integrated_excel(compiled_bat, compiled_pit)
    st.download_button(
        "📥 打撃・投手・選手別シート付き 統合Excelをダウンロード",
        data=excel_bin,
        file_name="学童野球_チーム統合成績一覧.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
