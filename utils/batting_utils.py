import io
import pandas as pd
from PIL import Image, ImageEnhance

# 打席結果の完全選択肢（公式記録ルール準拠）
RESULT_OPTIONS = [
    "なし",
    "単打",
    "二塁打",
    "三塁打",
    "本塁打",
    "四球",
    "死球",
    "犠打",
    "犠飛",
    "凡打",
    "三振",
    "敵失",
    "野選",
    "振り逃げ"
]

def enhance_sharpness(pil_img: Image.Image) -> bytes:
    """高精細カラー解析のための鮮鋭化フィルター（コントラスト＆シャープネス強調）"""
    enhancer_contrast = ImageEnhance.Contrast(pil_img)
    img_contrasted = enhancer_contrast.enhance(1.4)
    enhancer_sharp = ImageEnhance.Sharpness(img_contrasted)
    img_sharp = enhancer_sharp.enhance(2.0)
    
    buf = io.BytesIO()
    img_sharp.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def calculate_stats_from_grid(players_data: list, match_file_name: str = "") -> list:
    """盤面グリッドから公式野球記録ルールに基づき成績を集計"""
    compiled_list = []
    
    for p in players_data:
        p_name = str(p.get("player_name", "")).strip()
        u_num = str(p.get("uniform_number", "")).strip()
        innings = p.get("innings", {})
        rbi = int(p.get("rbi", 0))
        sb = int(p.get("stolen_bases", 0))
        hl = str(p.get("highlight", "")).strip()

        plate_appearances = 0
        at_bats = 0
        hits = 0
        doubles = 0
        triples = 0
        homeruns = 0
        walks = 0
        deadballs = 0
        strikeouts = 0
        sacrifice_hits = 0
        sacrifice_flies = 0

        for inn_str, res in innings.items():
            if not res or res in ["なし", "要確認"]:
                continue
            
            plate_appearances += 1

            if res == "単打":
                at_bats += 1
                hits += 1
            elif res in ["二塁打", "2塁打"]:
                at_bats += 1
                doubles += 1
            elif res in ["三塁打", "3塁打"]:
                at_bats += 1
                triples += 1
            elif res == "本塁打":
                at_bats += 1
                homeruns += 1
            elif res == "四球":
                walks += 1
            elif res == "死球":
                deadballs += 1
            elif res == "犠打":
                sacrifice_hits += 1
            elif res == "犠飛":
                sacrifice_flies += 1
            elif res == "凡打":
                at_bats += 1
            elif res == "三振":
                at_bats += 1
                strikeouts += 1
            elif res == "敵失":
                at_bats += 1
            elif res == "野選":
                at_bats += 1
            elif res == "振り逃げ":
                at_bats += 1
                strikeouts += 1

        compiled_list.append({
            "source_file": match_file_name,
            "batting_order": p.get("batting_order", 0),
            "uniform_number": u_num,
            "player_name": p_name,
            "is_substitute": p.get("is_substitute", False),
            "plate_appearances": plate_appearances,
            "at_bats": at_bats,
            "hits": hits,
            "doubles": doubles,
            "triples": triples,
            "homeruns": homeruns,
            "walks": walks,
            "deadballs": deadballs,
            "strikeouts": strikeouts,
            "sacrifice_hits": sacrifice_hits,
            "sacrifice_flies": sacrifice_flies,
            "rbi": rbi,
            "stolen_bases": sb,
            "highlight": hl
        })

    return compiled_list

def create_excel_from_compiled(compiled_records: list) -> bytes:
    """全試合統合成績および選手個別シート付きのExcelバイナリを生成（選手名基準で1人1行に統合）"""
    if not compiled_records:
        return b""

    df_raw = pd.DataFrame(compiled_records)

    # 1. 表示用の日本語カラム名への変換マップ
    col_rename = {
        "source_file": "試合ファイル",
        "batting_order": "打順",
        "uniform_number": "背番号",
        "player_name": "選手名",
        "is_substitute": "交代/代打",
        "plate_appearances": "打席数",
        "at_bats": "打数",
        "hits": "安打",
        "doubles": "二塁打",
        "triples": "三塁打",
        "homeruns": "本塁打",
        "walks": "四球",
        "deadballs": "死球",
        "strikeouts": "三振",
        "sacrifice_hits": "犠打",
        "sacrifice_flies": "犠飛",
        "rbi": "打点",
        "stolen_bases": "盗塁",
        "highlight": "ハイライト"
    }
    df_detail = df_raw.rename(columns=col_rename)

    # 2. 選手名ごとに1人1行へ統合・集計
    # 空白を除去した選手名でグループ化
    df_raw["clean_name"] = df_raw["player_name"].astype(str).str.strip()
    # 空の名前は除外
    df_valid = df_raw[df_raw["clean_name"] != ""].copy()

    summary_rows = []
    grouped = df_valid.groupby("clean_name", sort=False)

    for p_name, group in grouped:
        # 背番号：空文字を除外した最新（最後）の試合の背番号を採用
        valid_nums = [str(n).strip() for n in group["uniform_number"] if str(n).strip()]
        rep_num = valid_nums[-1] if valid_nums else ""

        pa = int(group["plate_appearances"].sum())
        ab = int(group["at_bats"].sum())
        h = int(group["hits"].sum())
        d = int(group["doubles"].sum())
        t = int(group["triples"].sum())
        hr = int(group["homeruns"].sum())
        single = h - (d + t + hr)  # 単打
        bb = int(group["walks"].sum())
        hbp = int(group["deadballs"].sum())
        so = int(group["strikeouts"].sum())
        sh = int(group["sacrifice_hits"].sum())
        sf = int(group["sacrifice_flies"].sum())
        rbi = int(group["rbi"].sum())
        sb = int(group["stolen_bases"].sum())

        # 塁打
        tb = single + (d * 2) + (t * 3) + (hr * 4)

        # 打率
        avg_str = f"{(h / ab):.3f}".lstrip("0") if ab > 0 else "---"
        if avg_str.startswith("."):
            avg_str = "." + avg_str[1:]
        elif ab > 0 and h == ab:
            avg_str = "1.000"

        # 出塁率 = (安打 + 四球 + 死球) / (打数 + 四球 + 死球 + 犠飛)
        obp_denom = ab + bb + hbp + sf
        obp_val = (h + bb + hbp) / obp_denom if obp_denom > 0 else 0.0
        obp_str = f"{obp_val:.3f}".lstrip("0") if obp_denom > 0 else "---"
        if obp_str.startswith("."):
            obp_str = "." + obp_str[1:]
        elif obp_denom > 0 and (h + bb + hbp) == obp_denom:
            obp_str = "1.000"

        # 長打率 = 塁打 / 打数
        slg_val = tb / ab if ab > 0 else 0.0
        slg_str = f"{slg_val:.3f}".lstrip("0") if ab > 0 else "---"

        # OPS = 出塁率 + 長打率
        ops_str = f"{(obp_val + slg_val):.3f}" if (obp_denom > 0 or ab > 0) else "---"

        summary_rows.append({
            "背番号": rep_num,
            "選手名": p_name,
            "打席数": pa,
            "打数": ab,
            "安打": h,
            "単打": single,
            "二塁打": d,
            "三塁打": t,
            "本塁打": hr,
            "塁打": tb,
            "打点": rbi,
            "盗塁": sb,
            "四球": bb,
            "死球": hbp,
            "犠打": sh,
            "犠飛": sf,
            "三振": so,
            "打率": avg_str,
            "出塁率": obp_str,
            "長打率": slg_str,
            "OPS": ops_str
        })

    df_summary = pd.DataFrame(summary_rows)

    # 背番号順（数値としてソートできるものは数値順）で並べ替え
    def sort_key(val):
        try:
            return (0, int(val))
        except:
            return (1, str(val))
    
    if not df_summary.empty and "背番号" in df_summary.columns:
        df_summary["_sort"] = df_summary["背番号"].map(sort_key)
        df_summary = df_summary.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # 1シート目：選手名基準で1人1行にまとめた通算サマリー
        df_summary.to_excel(writer, sheet_name="シーズン通算打撃サマリー", index=False)

        # 2シート目：全試合の1打席ごとの明細データ
        df_detail.to_excel(writer, sheet_name="全試合明細データ", index=False)

        # 3シート目以降：選手ごとの個別シート
        players = df_detail["選手名"].dropna().unique()
        for player in players:
            p_str = str(player).strip()
            if not p_str:
                continue
            df_player = df_detail[df_detail["選手名"] == p_str]
            sheet_title = p_str[:28].replace("/", "_").replace("\\", "_").replace("?", "").replace("*", "")
            df_player.to_excel(writer, sheet_name=sheet_title, index=False)

    return output.getvalue()
