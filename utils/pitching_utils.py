import io
import pandas as pd
from PIL import Image, ImageEnhance

# 投球回（IP）の選択肢（学童野球対応：0.0回〜7.0回）
IP_OPTIONS = [
    0.0, 0.1, 0.2,
    1.0, 1.1, 1.2,
    2.0, 2.1, 2.2,
    3.0, 3.1, 3.2,
    4.0, 4.1, 4.2,
    5.0, 5.1, 5.2,
    6.0, 6.1, 6.2,
    7.0
]

# 勝敗の選択肢
DECISION_OPTIONS = [
    "なし",
    "勝利(W)",
    "敗戦(L)",
    "セーブ(S)"
]

def enhance_sharpness(pil_img: Image.Image) -> bytes:
    """高精細カラー解析のための鮮鋭化フィルター（赤ペン・失点丸・黒文字強調）"""
    enhancer_contrast = ImageEnhance.Contrast(pil_img)
    img_contrasted = enhancer_contrast.enhance(1.4)
    enhancer_sharp = ImageEnhance.Sharpness(img_contrasted)
    img_sharp = enhancer_sharp.enhance(2.0)
    
    buf = io.BytesIO()
    img_sharp.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def ip_to_fraction(ip_val: float) -> float:
    """
    投球回の端数（3.1 -> 3 + 1/3, 3.2 -> 3 + 2/3）を正確に実数換算する。
    学童野球の防御率計算で丸め誤差を出さないための必須ロジック。
    """
    full_inns = int(ip_val)
    frac_part = round(ip_val - full_inns, 1)
    if frac_part == 0.1:
        return full_inns + (1.0 / 3.0)
    elif frac_part == 0.2:
        return full_inns + (2.0 / 3.0)
    return float(full_inns)

def calculate_pitcher_stats_from_grid(pitchers_data: list, match_file_name: str = "") -> list:
    """盤面グリッドから学童公式野球規則（6回制）に基づき投手成績を集計"""
    compiled_pitchers = []
    
    for pt in pitchers_data:
        p_name = str(pt.get("pitcher_name", "")).strip()
        u_num = str(pt.get("uniform_number", "")).strip()
        ip_display = float(pt.get("innings_pitched", 0.0))
        actual_ip = ip_to_fraction(ip_display)
        
        pc = int(pt.get("pitch_count", 0))
        ha = int(pt.get("hits_allowed", 0))
        so = int(pt.get("strikeouts", 0))
        bb = int(pt.get("walks_allowed", 0))
        hbp = int(pt.get("hit_by_pitch", 0))
        ra = int(pt.get("runs_allowed", 0))
        er = int(pt.get("earned_runs", 0))
        dec = str(pt.get("decision", "なし"))

        # 防御率（学童公式 6回基準：自責点 × 6 ÷ 投球回）
        era = (er * 6.0 / actual_ip) if actual_ip > 0 else 0.0
        
        # WHIP（1イニングあたりの被安打・四死球率：(被安打 + 四球 + 死球) ÷ 投球回）
        whip = ((ha + bb + hbp) / actual_ip) if actual_ip > 0 else 0.0

        compiled_pitchers.append({
            "source_file": match_file_name,
            "uniform_number": u_num,
            "player_name": p_name,
            "innings_pitched": ip_display,
            "actual_ip": round(actual_ip, 3),
            "pitch_count": pc,
            "hits_allowed": ha,
            "strikeouts": so,
            "walks_allowed": bb,
            "hit_by_pitch": hbp,
            "runs_allowed": ra,
            "earned_runs": er,
            "era": round(era, 2),
            "whip": round(whip, 2),
            "decision": dec
        })

    return compiled_pitchers

def create_pitcher_excel_from_compiled(compiled_pitchers: list) -> bytes:
    """全試合統合投手成績および投手個別シート付きのExcelバイナリを生成"""
    df_all = pd.DataFrame(compiled_pitchers)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_all.to_excel(writer, sheet_name="全投手成績一覧", index=False)

        # 投手ごとの個別シート
        pitchers = df_all["player_name"].dropna().unique()
        for pitcher in pitchers:
            if not str(pitcher).strip():
                continue
            df_pt = df_all[df_all["player_name"] == pitcher]
            sheet_title = str(pitcher)[:28].replace("/", "_").replace("\\", "_")
            df_pt.to_excel(writer, sheet_name=sheet_title, index=False)

    return output.getvalue()
