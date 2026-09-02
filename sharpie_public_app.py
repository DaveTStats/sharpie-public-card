from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
    from zoneinfo import ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Streamlit Cloud fallback for older Python images.
    from backports.zoneinfo import ZoneInfo
    from backports.zoneinfo import ZoneInfoNotFoundError

import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError


ROOT = Path(__file__).resolve().parent
SHARPIE_PICKS = ROOT / "data" / "processed" / "sharpie_picks.csv"
SHARPIE_WRITEUPS = ROOT / "data" / "processed" / "sharpie_writeups.csv"
SHARPIE_RESULTS_PUBLIC = ROOT / "data" / "processed" / "sharpie_results_public.csv"
PLAYER_LOOKUP = ROOT / "data" / "processed" / "sharpie_player_lookup_public.csv"
LIVE_BUYBACK_RANKINGS = ROOT / "data" / "processed" / "live_buyback_player_rankings.csv"
PARLAY_PREDICTOR_TODAY = ROOT / "data" / "processed" / "parlay_predictor_today.csv"
PARLAY_PREDICTOR_BACKTEST = ROOT / "data" / "processed" / "parlay_predictor_backtest.csv"
SHARPIE_PARLAYS = ROOT / "data" / "processed" / "sharpie_parlays.csv"
SHARPIE_BEST_PARLAY_LOCKED = ROOT / "data" / "processed" / "sharpie_best_parlay_locked.csv"
SHARPIE_TOP3_PARLAY_BACKTEST = ROOT / "data" / "processed" / "sharpie_top3_only_parlay_backtest.csv"
SHARPIE_SOL_LATEST = ROOT / "data" / "processed" / "sharpie_sol_latest.json"
ANALYSIS_DIR = ROOT / "outputs" / "analysis"
SHARPIE_EXCLUDED_PERFORMANCE_DATES = {"2026-05-23"}
try:
    LOCAL_TIMEZONE = ZoneInfo("America/Indianapolis")
except ZoneInfoNotFoundError:  # Windows local fallback when tzdata is not installed.
    LOCAL_TIMEZONE = dt.timezone(dt.timedelta(hours=-4), name="America/Indianapolis")


st.set_page_config(page_title="Sharpie MLB Hit Card", page_icon="Sharpie", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 0%, rgba(255,106,0,.22), transparent 28%),
                    linear-gradient(135deg, #07111f 0%, #0b1724 42%, #130d08 100%);
        color: #f8fafc;
    }
    .block-container { padding-top: 1.4rem; max-width: 1180px; }
    .hero {
        border: 1px solid rgba(255,106,0,.45);
        border-radius: 18px;
        padding: 24px;
        background: linear-gradient(135deg, rgba(10,18,30,.94), rgba(20,14,8,.90));
        box-shadow: 0 0 35px rgba(255,106,0,.18);
    }
    .brand { font-size: 3rem; font-weight: 900; font-style: italic; letter-spacing: .02em; }
    .tag { color: #ffbf3f; font-weight: 800; text-transform: uppercase; letter-spacing: .12em; }
    .card {
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 14px;
        padding: 18px;
        background: rgba(5, 12, 21, .78);
        min-height: 120px;
    }
    .pick {
        border: 1px solid rgba(255,106,0,.55);
        border-radius: 16px;
        padding: 20px;
        background: linear-gradient(135deg, rgba(255,106,0,.13), rgba(8,15,25,.86));
        box-shadow: inset 0 0 25px rgba(255,106,0,.08);
    }
    .pick.locked {
        border-color: rgba(98,210,111,.72);
        background: linear-gradient(135deg, rgba(98,210,111,.15), rgba(8,15,25,.90));
        box-shadow: 0 0 24px rgba(98,210,111,.12), inset 0 0 25px rgba(98,210,111,.08);
    }
    .hold-card {
        border: 1px dashed rgba(255,191,63,.72);
        border-radius: 16px;
        padding: 20px;
        background: linear-gradient(135deg, rgba(255,191,63,.10), rgba(8,15,25,.82));
        box-shadow: inset 0 0 20px rgba(255,191,63,.06);
    }
    .status-badge {
        display: inline-block;
        margin-left: 10px;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 950;
        letter-spacing: .08em;
        text-transform: uppercase;
        vertical-align: middle;
    }
    .status-locked {
        color: #7dff8e;
        border: 1px solid rgba(98,210,111,.80);
        background: rgba(98,210,111,.18);
        box-shadow: 0 0 16px rgba(98,210,111,.20);
    }
    .status-hold {
        color: #ffcf6f;
        border: 1px solid rgba(255,191,63,.75);
        background: rgba(255,191,63,.14);
    }
    .sol-badge {
        display: inline-block;
        margin-left: 10px;
        padding: 4px 10px;
        border-radius: 999px;
        color: #7dff8e;
        border: 1px solid rgba(98,210,111,.80);
        background: rgba(98,210,111,.18);
        font-size: .76rem;
        font-weight: 950;
        letter-spacing: .06em;
        vertical-align: middle;
    }
    .sol-risk-badge {
        color: #ff9aa5;
        border-color: rgba(255,91,107,.82);
        background: rgba(255,91,107,.16);
    }
    .status-explainer {
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 14px;
        padding: 14px 16px;
        background: rgba(5, 12, 21, .68);
        margin: 18px 0;
    }
    .money-muted {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 800;
    }
    .label { color: #aab6c5; font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }
    .big { font-size: 1.9rem; font-weight: 900; }
    .accent { color: #ffbf3f; }
    .good { color: #62d26f; }
    .warn { color: #ffbf3f; }
    .bad { color: #ff5b6b; }
    div[data-testid="stMetric"],
    div[data-testid="metric-container"] {
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 14px;
        padding: 12px 14px;
        background: rgba(5, 12, 21, .66);
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] label {
        color: #ffbf3f !important;
        font-weight: 850 !important;
        letter-spacing: .02em;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important;
        font-weight: 950 !important;
        text-shadow: 0 0 12px rgba(255,191,63,.14);
    }
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] div,
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p {
        color: #c7d2fe !important;
    }
    .tracked-performance-title,
    .tracked-performance-title h2 {
        color: #ffbf3f !important;
        font-weight: 950 !important;
        text-shadow: 0 0 16px rgba(255,191,63,.22);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 0;
        margin: 10px 0 18px;
    }
    .stTabs [data-baseweb="tab"] {
        border: 1px solid rgba(98,210,111,.62);
        border-radius: 999px;
        padding: 8px 18px;
        min-height: 38px;
        background: rgba(98,210,111,.12);
        color: #d7ffe0;
        font-weight: 950;
        letter-spacing: .02em;
        box-shadow: inset 0 0 16px rgba(98,210,111,.08);
    }
    .stTabs [data-baseweb="tab"] p {
        color: #d7ffe0;
        font-weight: 950;
        font-size: .98rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(98,210,111,.95), rgba(37,155,72,.88));
        border-color: rgba(166,255,178,.95);
        box-shadow: 0 0 22px rgba(98,210,111,.28), inset 0 0 18px rgba(255,255,255,.10);
    }
    .stTabs [aria-selected="true"] p {
        color: #06130a;
        text-shadow: none;
    }
    .roi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin: 18px 0;
    }
    .roi-card {
        border: 1px solid rgba(98,210,111,.55);
        border-radius: 16px;
        padding: 18px;
        background: linear-gradient(135deg, rgba(98,210,111,.13), rgba(8,15,25,.86));
        box-shadow: 0 0 24px rgba(98,210,111,.10), inset 0 0 25px rgba(98,210,111,.06);
        min-height: 210px;
    }
    .roi-rank {
        color: #7dff8e;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: .10em;
        font-size: .78rem;
    }
    .roi-metric-row {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 8px;
        margin-top: 12px;
    }
    .roi-mini {
        border: 1px solid rgba(255,255,255,.10);
        border-radius: 10px;
        padding: 8px;
        background: rgba(5, 12, 21, .58);
    }
    .roi-mini .value {
        font-size: 1.15rem;
        font-weight: 950;
        color: #f8fafc;
    }
    .parlay-card {
        border: 1px solid rgba(255,191,63,.62);
        border-radius: 18px;
        padding: 18px;
        background: linear-gradient(135deg, rgba(255,191,63,.15), rgba(7,12,21,.90));
        box-shadow: 0 0 28px rgba(255,191,63,.12), inset 0 0 24px rgba(255,191,63,.06);
        margin: 12px 0 18px;
    }
    .parlay-leg-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
        margin-top: 14px;
    }
    .parlay-leg {
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 14px;
        padding: 12px;
        background: rgba(5, 12, 21, .65);
    }
    .parlay-tag {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: .76rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: #06130a;
        background: #ffbf3f;
        margin-left: 8px;
    }
    .sharpie-stage {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 106, 0, .38);
        background:
            radial-gradient(circle at 18% 20%, rgba(255, 191, 63, .22), transparent 26%),
            linear-gradient(135deg, rgba(8, 13, 21, .96), rgba(18, 26, 38, .90));
        border-radius: 18px;
        padding: 18px;
        min-height: 330px;
        margin-bottom: 18px;
        box-shadow: 0 18px 60px rgba(0,0,0,.32), inset 0 0 0 1px rgba(255,255,255,.05);
    }
    .sharpie-logo {
        position: absolute;
        left: 22px;
        top: 16px;
        color: #f8fbff;
        font-size: 40px;
        font-weight: 900;
        font-style: italic;
        text-shadow: 0 0 22px rgba(255,106,0,.35);
    }
    .sharpie-tagline {
        position: absolute;
        left: 26px;
        top: 68px;
        color: #ffbf3f;
        font-size: 12px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: .10em;
    }
    .sharpie-date {
        position: absolute;
        left: 26px;
        top: 94px;
        color: #94a3b8;
        font-size: .95rem;
    }
    .sharpie-character {
        position: absolute;
        left: 50px;
        bottom: 18px;
        width: 210px;
        height: 240px;
        animation: sharpie-bob 3.4s ease-in-out infinite;
        transform-origin: 50% 100%;
    }
    .sharpie-head {
        position: absolute;
        left: 70px;
        top: 34px;
        width: 88px;
        height: 82px;
        background: linear-gradient(145deg, #d49158, #9f5b35);
        border-radius: 44% 44% 48% 48%;
        box-shadow: inset -8px -8px 0 rgba(60,24,13,.12);
    }
    .sharpie-cap {
        position: absolute;
        left: 58px;
        top: 16px;
        width: 112px;
        height: 46px;
        background: linear-gradient(180deg, #101826, #050811);
        border-radius: 52px 52px 18px 18px;
        transform: rotate(-4deg);
        z-index: 3;
        box-shadow: 0 5px 0 rgba(0,0,0,.30);
    }
    .sharpie-cap::after {
        content: "";
        position: absolute;
        right: -24px;
        bottom: 2px;
        width: 50px;
        height: 16px;
        background: #080c14;
        border-radius: 50%;
        transform: rotate(8deg);
    }
    .sharpie-cap span {
        position: absolute;
        left: 26px;
        top: 11px;
        color: #fff3d7;
        font-size: 16px;
        font-weight: 900;
        font-style: italic;
        transform: rotate(-5deg);
    }
    .sharpie-pencil {
        position: absolute;
        left: 46px;
        top: 48px;
        width: 46px;
        height: 6px;
        background: linear-gradient(90deg, #f4c542 78%, #1d2636 78%);
        border-radius: 4px;
        transform: rotate(-24deg);
        z-index: 2;
    }
    .sharpie-eye {
        position: absolute;
        top: 34px;
        width: 8px;
        height: 8px;
        background: #17202f;
        border-radius: 50%;
        animation: sharpie-blink 5.2s infinite;
    }
    .sharpie-eye.left { left: 22px; }
    .sharpie-eye.right { right: 24px; }
    .sharpie-smile {
        position: absolute;
        left: 28px;
        top: 52px;
        width: 38px;
        height: 16px;
        border-bottom: 6px solid #fff8ed;
        border-radius: 0 0 50px 50px;
    }
    .sharpie-beard {
        position: absolute;
        left: 15px;
        bottom: 5px;
        width: 58px;
        height: 22px;
        border-bottom: 11px solid rgba(35,20,17,.62);
        border-radius: 0 0 48px 48px;
    }
    .sharpie-body {
        position: absolute;
        left: 48px;
        bottom: 16px;
        width: 126px;
        height: 132px;
        background: linear-gradient(90deg, #f4f1e8 0 22%, #0b1220 22% 76%, #f4f1e8 76%);
        border-radius: 28px 28px 18px 18px;
        border: 2px solid rgba(255,255,255,.22);
        box-shadow: inset 0 -18px 0 rgba(0,0,0,.10);
    }
    .sharpie-body::after {
        content: "31";
        position: absolute;
        right: 19px;
        top: 56px;
        color: #101826;
        font-weight: 900;
        font-size: 22px;
    }
    .sharpie-chain {
        position: absolute;
        left: 92px;
        top: 104px;
        width: 46px;
        height: 46px;
        border: 3px solid rgba(255,191,63,.75);
        border-top: 0;
        border-radius: 0 0 36px 36px;
        z-index: 5;
    }
    .sharpie-phone {
        position: absolute;
        left: 10px;
        top: 96px;
        width: 42px;
        height: 78px;
        background: #070b12;
        border: 3px solid #1f2b3d;
        border-radius: 10px;
        transform: rotate(-8deg);
        animation: sharpie-phone-glow 2.8s ease-in-out infinite;
        z-index: 7;
    }
    .sharpie-phone::before {
        content: "-135\\A+105\\A-195";
        white-space: pre;
        position: absolute;
        left: 8px;
        top: 13px;
        color: #62d26f;
        font-size: 9px;
        line-height: 1.45;
        font-weight: 900;
    }
    .sharpie-slip {
        position: absolute;
        right: 8px;
        top: 112px;
        width: 52px;
        height: 72px;
        background: #fff5dd;
        color: #0d1724;
        border-radius: 4px;
        transform: rotate(9deg);
        box-shadow: 0 8px 20px rgba(0,0,0,.20);
        z-index: 8;
    }
    .sharpie-slip::before {
        content: "HIT CARD\\A +EDGE\\A ROI";
        white-space: pre;
        position: absolute;
        left: 7px;
        top: 9px;
        font-size: 8px;
        line-height: 1.55;
        font-weight: 900;
    }
    .sharpie-bubbles {
        position: absolute;
        left: 320px;
        right: 20px;
        top: 30px;
        display: grid;
        grid-template-columns: repeat(3, minmax(180px, 1fr));
        gap: 12px;
        color: #eaf3ff;
    }
    .sharpie-bubble {
        border: 1px solid rgba(255,255,255,.13);
        background: rgba(7, 10, 16, .62);
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
        min-height: 94px;
    }
    .sharpie-bubble strong { color: #ffbf3f; }
    @keyframes sharpie-bob {
        0%, 100% { transform: translateY(0) rotate(-1deg); }
        50% { transform: translateY(-8px) rotate(1deg); }
    }
    @keyframes sharpie-blink {
        0%, 92%, 100% { transform: scaleY(1); }
        95% { transform: scaleY(.12); }
    }
    @keyframes sharpie-phone-glow {
        0%, 100% { box-shadow: 0 0 0 rgba(98,210,111,0); }
        50% { box-shadow: 0 0 18px rgba(98,210,111,.42); }
    }
    @media (max-width: 760px) {
        .sharpie-stage { min-height: 520px; }
        .sharpie-character {
            left: 50%;
            transform: translateX(-50%);
            bottom: 16px;
        }
        .sharpie-bubbles {
            left: 14px;
            right: 14px;
            top: 120px;
            display: block;
        }
        .sharpie-bubble {
            min-height: auto;
            margin-bottom: 10px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def read_json(path: Path) -> dict[str, object]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@st.cache_data(ttl=60)
def read_latest_csv(pattern: str) -> tuple[pd.DataFrame, str]:
    def dated_sort_key(item: Path) -> tuple[pd.Timestamp, float]:
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", item.name)
        file_date = pd.to_datetime(match.group(1), errors="coerce") if match else pd.NaT
        if pd.isna(file_date):
            file_date = pd.Timestamp.min
        return file_date, item.stat().st_mtime

    files = sorted(ANALYSIS_DIR.glob(pattern), key=dated_sort_key, reverse=True)
    if not files:
        return pd.DataFrame(), ""
    try:
        return pd.read_csv(files[0]), files[0].stem
    except EmptyDataError:
        return pd.DataFrame(), files[0].stem


def num(series: pd.Series | object, default: float = 0.0) -> pd.Series:
    if isinstance(series, pd.Series):
        return pd.to_numeric(series, errors="coerce").fillna(default)
    return pd.Series(dtype=float)


def pct(value: object) -> str:
    try:
        value = float(value)
    except Exception:
        return "--"
    if pd.isna(value):
        return "--"
    return f"{value:.1%}"


def money(value: object) -> str:
    try:
        value = float(value)
    except Exception:
        return "--"
    if pd.isna(value):
        return "--"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def latest_date(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return dt.date.today().isoformat()
    dates = frame[column].dropna().astype(str)
    return dates.max() if not dates.empty else dt.date.today().isoformat()


def refresh_game_timing(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    source = None
    if "commence_time" in out.columns:
        source = out["commence_time"].replace(r"^\s*$", pd.NA, regex=True)
    if "game_start_local" in out.columns:
        fallback = out["game_start_local"].replace(r"^\s*$", pd.NA, regex=True)
        source = fallback if source is None else source.combine_first(fallback)
    if source is None:
        return out

    def parse_game_time(value):
        if pd.isna(value):
            return pd.NaT
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            return pd.NaT
        return parsed.tz_convert(LOCAL_TIMEZONE)

    starts = source.apply(parse_game_time)
    out["game_start_local"] = starts.apply(lambda value: value.isoformat(timespec="minutes") if pd.notna(value) else "")
    now = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
    out["minutes_to_game"] = ((starts - now).dt.total_seconds() / 60.0).round(1)
    return out


def value(row: pd.Series, column: str, default: float = 0.0) -> float:
    raw = row.get(column, default)
    try:
        parsed = float(raw)
    except Exception:
        return default
    return default if pd.isna(parsed) else parsed


def truthy(raw: object) -> bool:
    return str(raw).strip().lower() in {"true", "1", "yes", "y"}


def clamp(number: float, low: float, high: float) -> float:
    return max(low, min(high, number))


def odds_text(raw: object) -> str:
    try:
        odds = int(float(raw))
    except Exception:
        return "--"
    return f"+{odds}" if odds > 0 else str(odds)


def roi_edge_latest_targets() -> tuple[pd.DataFrame, str]:
    current, current_label = read_latest_csv("roi_edge_current_card_*.csv")
    locked, label = read_latest_csv("roi_edge_locked_card_*.csv")

    if not current.empty:
        current = current.copy()
        current["display_roi_rank"] = pd.to_numeric(current.get("roi_edge_card_pick"), errors="coerce")
        current_targets = current[current["display_roi_rank"].isin([1, 3, 5])].copy()

        locked_targets = pd.DataFrame()
        if not locked.empty:
            locked = locked.copy()
            locked_rank_col = "roi_edge_locked_rank" if "roi_edge_locked_rank" in locked.columns else "roi_edge_card_pick"
            locked["display_roi_rank"] = pd.to_numeric(locked.get(locked_rank_col), errors="coerce")
            locked_status = locked.get("roi_edge_lock_status", pd.Series("", index=locked.index)).astype(str).str.upper()
            locked_targets = locked[locked["display_roi_rank"].isin([1, 3, 5]) & locked_status.eq("LOCKED")].copy()

        rows: list[pd.Series] = []
        for rank in [1, 3, 5]:
            locked_rank = locked_targets[locked_targets["display_roi_rank"].eq(rank)] if not locked_targets.empty else pd.DataFrame()
            if not locked_rank.empty:
                row = locked_rank.iloc[-1].copy()
                row["display_roi_status"] = "LOCKED"
                rows.append(row)
                continue

            current_rank = current_targets[current_targets["display_roi_rank"].eq(rank)]
            if not current_rank.empty:
                row = current_rank.iloc[0].copy()
                row["display_roi_status"] = "HOLD"
                rows.append(row)

        if not rows:
            return pd.DataFrame(), current_label
        targets = pd.DataFrame(rows)
        targets["display_roi_rank"] = pd.to_numeric(targets.get("display_roi_rank"), errors="coerce").astype("Int64")
        source_label = label if not locked_targets.empty else current_label
        return targets.sort_values("display_roi_rank"), source_label

    if locked.empty:
        return locked, label

    rank_col = "roi_edge_locked_rank" if "roi_edge_locked_rank" in locked.columns else "roi_edge_card_pick"
    locked[rank_col] = pd.to_numeric(locked.get(rank_col), errors="coerce")
    locked = locked[locked[rank_col].isin([1, 3, 5])].copy()
    locked["display_roi_rank"] = locked[rank_col].astype("Int64")
    locked["display_roi_status"] = "LOCKED"
    return locked.sort_values("display_roi_rank"), label


def roi_edge_rank_performance() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    daily, label = read_latest_csv("roi_edge_pa_path_rank_daily_*.csv")
    all_time, _ = read_latest_csv("roi_edge_pa_path_rank_summary_*.csv")
    if daily.empty:
        return daily, all_time, label
    daily = daily.copy()
    daily["date_dt"] = pd.to_datetime(daily.get("date"), errors="coerce")
    daily["roi_card_rank"] = pd.to_numeric(daily.get("roi_card_rank"), errors="coerce")
    daily["actual_hit"] = pd.to_numeric(daily.get("actual_hit"), errors="coerce")
    daily["profit"] = pd.to_numeric(daily.get("profit"), errors="coerce")
    daily["odds"] = pd.to_numeric(daily.get("odds"), errors="coerce")
    daily = daily[daily["roi_card_rank"].isin([1, 3, 5]) & daily["actual_hit"].isin([0, 1])].copy()
    if daily.empty:
        return daily, all_time, label
    if all_time.empty:
        all_time = (
            daily.groupby("roi_card_rank", as_index=False)
            .agg(
                picks=("actual_hit", "size"),
                hits=("actual_hit", "sum"),
                hit_rate=("actual_hit", "mean"),
                profit=("profit", "sum"),
                avg_odds=("odds", "mean"),
            )
            .sort_values("roi_card_rank")
        )
        all_time["roi"] = all_time["profit"] / all_time["picks"].replace(0, pd.NA)
    else:
        all_time = all_time.copy()
        all_time["roi_card_rank"] = pd.to_numeric(all_time.get("roi_card_rank"), errors="coerce")
        for column in ["picks", "hits", "hit_rate", "profit", "roi", "avg_odds"]:
            if column in all_time.columns:
                all_time[column] = pd.to_numeric(all_time[column], errors="coerce")
        all_time = all_time[all_time["roi_card_rank"].isin([1, 3, 5])].copy().sort_values("roi_card_rank")
    return daily.sort_values(["date_dt", "roi_card_rank"], ascending=[False, True]), all_time, label


def live_buyback_board(run_date: str) -> pd.DataFrame:
    today_path = ROOT / "data" / "processed" / f"live_buyback_watchlist_{run_date}.csv"
    board = read_csv(today_path)
    source_path = today_path if not board.empty else LIVE_BUYBACK_RANKINGS
    if board.empty:
        board = read_csv(LIVE_BUYBACK_RANKINGS)
    if board.empty:
        return board
    board = board.copy()
    try:
        updated_at = dt.datetime.fromtimestamp(source_path.stat().st_mtime, tz=LOCAL_TIMEZONE).isoformat(timespec="minutes")
    except OSError:
        updated_at = ""
    board["_source_updated_at"] = updated_at
    for column in [
        "buyback_watch_score",
        "buyback_score",
        "bayes_recovery_hit_rate",
        "recovery_hit_rate_after_0for1",
        "fair_live_odds_after_0for1",
        "current_dk_hit_odds",
        "odds",
        "pregame_to_0for1_fair_odds_move",
        "first_pa_no_hit_games",
        "avg_remaining_pa_after_0for1",
        "today_lineup_slot",
        "projected_pa",
        "sharpie_late_hitter_slot",
    ]:
        if column in board.columns:
            board[column] = pd.to_numeric(board[column], errors="coerce")
    sort_col = "buyback_watch_score" if "buyback_watch_score" in board.columns else "buyback_score"
    if "sharpie_late_hitter_reserved" in board.columns:
        reserved = board["sharpie_late_hitter_reserved"].astype(str).str.lower().isin(["true", "1", "1.0", "yes"])
        board = board[reserved].copy()
        if "sharpie_late_hitter_slot" in board.columns:
            return board.sort_values(["sharpie_late_hitter_slot", sort_col], ascending=[True, False]).head(5).copy()
        return board.sort_values(sort_col, ascending=False).head(5).copy()
    else:
        board = board.sort_values(sort_col, ascending=False).head(30).copy()
        if "team" in board.columns and "opponent" in board.columns:
            board["_game_key"] = board.apply(
                lambda row: " vs ".join(sorted([str(row.get("team", "")), str(row.get("opponent", ""))])),
                axis=1,
            )
            selected_indices = []
            game_counts = {}
            for idx, row in board.iterrows():
                game_key = str(row.get("_game_key", ""))
                if game_counts.get(game_key, 0) >= 2:
                    continue
                selected_indices.append(idx)
                game_counts[game_key] = game_counts.get(game_key, 0) + 1
                if len(selected_indices) == 5:
                    break
            if len(selected_indices) < 5:
                selected_indices.extend([idx for idx in board.index if idx not in selected_indices][: 5 - len(selected_indices)])
            return board.loc[selected_indices].copy()
        return board.head(5).copy()


def parlay_performance_rows() -> pd.DataFrame:
    rows = []

    predictor = read_csv(PARLAY_PREDICTOR_BACKTEST)
    if not predictor.empty:
        work = predictor.copy()
        for column in ["actual_parlay_hit", "profit", "combined_american_odds", "parlay_probability"]:
            if column in work.columns:
                work[column] = pd.to_numeric(work[column], errors="coerce")
        work = work[work["actual_parlay_hit"].isin([0, 1])].copy()
        rule_sets = [
            ("Predictor A: Prob >=44%, Odds <=+140", work[work["parlay_probability"].ge(0.44) & work["combined_american_odds"].le(140)]),
            ("Predictor B: Odds <=+160", work[work["combined_american_odds"].le(160)]),
        ]
        for label, subset in rule_sets:
            if subset.empty:
                continue
            rows.append(
                {
                    "Strategy": label,
                    "Sample": len(subset),
                    "Wins": int(subset["actual_parlay_hit"].sum()),
                    "Win Rate": subset["actual_parlay_hit"].mean(),
                    "ROI / 1u": subset["profit"].mean(),
                    "Avg Odds": subset["combined_american_odds"].mean(),
                }
            )

    top3 = read_csv(SHARPIE_TOP3_PARLAY_BACKTEST)
    if not top3.empty:
        work = top3.copy()
        for column in ["actual_parlay_hit", "profit", "recommended_stake", "combined_american_odds", "leg1_odds", "leg2_odds"]:
            if column in work.columns:
                work[column] = pd.to_numeric(work[column], errors="coerce")
        work = work[work["actual_parlay_hit"].isin([0, 1])].copy()
        stake = work.get("recommended_stake", pd.Series(1.0, index=work.index)).replace(0, pd.NA).fillna(1.0)
        work["_profit_per_1u"] = work["profit"] / stake
        subset = work[work["combined_american_odds"].le(140) & work["leg1_odds"].ge(-245) & work["leg2_odds"].ge(-245)].copy()
        if not subset.empty:
            rows.append(
                {
                    "Strategy": "Top-3 Backup: Odds <=+140, legs >=-245",
                    "Sample": len(subset),
                    "Wins": int(subset["actual_parlay_hit"].sum()),
                    "Win Rate": subset["actual_parlay_hit"].mean(),
                    "ROI / 1u": subset["_profit_per_1u"].mean(),
                    "Avg Odds": subset["combined_american_odds"].mean(),
                }
            )

    return pd.DataFrame(rows)


def current_best_parlay(run_date: str) -> tuple[pd.Series | None, str, str, str]:
    locked = read_csv(SHARPIE_BEST_PARLAY_LOCKED)
    if not locked.empty:
        locked = locked.copy()
        if "pick_date" in locked.columns:
            locked = locked[locked["pick_date"].astype(str).eq(str(run_date))].copy()
        if not locked.empty:
            row = locked.iloc[-1]
            locked_status = str(row.get("app_status", row.get("lock_status", "LOCKED")) or "LOCKED").upper()
            display_status = "LOCKED" if locked_status != "PASS" else "LOCKED PASS"
            grade = str(row.get("app_grade", row.get("parlay_grade", "Locked Parlay")) or "Locked Parlay")
            reason = str(row.get("lock_reason", "") or "This parlay snapshot is frozen and will not rotate on later refreshes.")
            note = f"{reason} Original read: {locked_status}."
            return row, display_status, grade, note

    predictor = read_csv(PARLAY_PREDICTOR_TODAY)
    if not predictor.empty:
        predictor = predictor.copy()
        for column in [
            "parlay_probability",
            "combined_american_odds",
            "parlay_ev_per_dollar",
            "parlay_predictor_score",
            "leg1_odds",
            "leg2_odds",
            "leg1_probability",
            "leg2_probability",
            "leg1_lineup_slot",
            "leg2_lineup_slot",
        ]:
            if column in predictor.columns:
                predictor[column] = pd.to_numeric(predictor[column], errors="coerce")
        if "pick_date" in predictor.columns:
            latest = latest_date(predictor, "pick_date")
            if latest:
                predictor = predictor[predictor["pick_date"].astype(str).eq(str(latest))].copy()

        primary = predictor[
            predictor["parlay_probability"].ge(0.44)
            & predictor["combined_american_odds"].le(140)
            & predictor["leg1_odds"].ge(-275)
            & predictor["leg2_odds"].ge(-275)
        ].copy()
        if not primary.empty:
            row = primary.sort_values(["parlay_probability", "parlay_ev_per_dollar", "parlay_predictor_score"], ascending=False).iloc[0]
            return row, "HOLD", "Grade A - Predictor A", "Live candidate only. It clears the strongest historical rule, but it can rotate until the earliest leg reaches the 60-minute lock window."

        secondary = predictor[
            predictor["combined_american_odds"].le(160)
            & predictor["leg1_odds"].ge(-275)
            & predictor["leg2_odds"].ge(-275)
        ].copy()
        if not secondary.empty:
            row = secondary.sort_values(["parlay_probability", "parlay_ev_per_dollar", "parlay_predictor_score"], ascending=False).iloc[0]
            return row, "HOLD", "Grade B - Predictor B", "Live candidate only. It uses the broader controlled-price rule, but it can rotate until the earliest leg reaches the 60-minute lock window."

        if not predictor.empty:
            row = predictor.sort_values(["parlay_probability", "parlay_ev_per_dollar", "parlay_predictor_score"], ascending=False).iloc[0]
            return row, "HOLD", "No Grade - Predictor Watchlist", "Best available parlay does not clear Sharpie's controlled-price filters yet and remains live until the lock window."

    official = read_csv(SHARPIE_PARLAYS)
    if official.empty:
        return None, "NO CARD", "No Parlay Data", "No parlay file has been published yet."
    official = official.copy()
    for column in ["combined_american_odds", "parlay_probability", "parlay_ev_per_dollar"]:
        if column in official.columns:
            official[column] = pd.to_numeric(official[column], errors="coerce")
    if "pick_date" in official.columns:
        latest = latest_date(official, "pick_date")
        if latest:
            official = official[official["pick_date"].astype(str).eq(str(latest))].copy()
    if official.empty:
        return None, "NO CARD", "No Current Parlay", "No current parlay row is available."
    row = official.sort_values(["parlay_probability", "parlay_ev_per_dollar"], ascending=False).iloc[0]
    raw_status = str(row.get("bet_status", "") or "").upper()
    status = "LOCKED" if raw_status == "LOCKED" else "HOLD"
    grade = "Grade C - Top 3 Backup" if status == "BET CANDIDATE" else "No Grade - Official Watchlist"
    return row, status, grade, "Using Sharpie's official parlay file because the predictor card was not available."


def render_best_parlay_tab(run_date: str) -> None:
    st.markdown("## Sharpie's Best 2-Leg Parlay")
    st.caption("This uses the historical parlay edge Sharpie found: controlled two-leg prices, preferably +140 or shorter, with modeled parlay probability of 44%+.")
    row, status, rule, note = current_best_parlay(run_date)
    perf_rows = parlay_performance_rows()

    if row is None:
        st.info(note)
    else:
        badge_class = "status-locked" if status.startswith("LOCKED") else "status-hold"
        stake_note = "Small 0.25u to 0.50u only" if status == "LOCKED" else "$0 until this card locks"
        st.markdown(
            f"""
            <div class="parlay-card">
              <div class="label">Sharpie Parlay Read <span class="status-badge {badge_class}">{status}</span><span class="parlay-tag">{rule}</span></div>
              <div class="big">{row.get('leg1_player', '')} + {row.get('leg2_player', '')}</div>
              <div>Combined odds: <strong>{odds_text(row.get('combined_american_odds'))}</strong> | Modeled parlay probability: <strong>{pct(row.get('parlay_probability'))}</strong> | EV/$: <strong>{pct(row.get('parlay_ev_per_dollar', row.get('parlay_edge')))}</strong></div>
              <div style="color:#aab6c5;margin-top:8px;">{note} Recommended sizing: <strong>{stake_note}</strong>.</div>
              <div class="parlay-leg-grid">
                <div class="parlay-leg">
                  <div class="label">Leg 1</div>
                  <div class="big">{row.get('leg1_player', '')}</div>
                  <div>{row.get('leg1_team', '')} vs {row.get('leg1_opponent', '')}</div>
                  <div>Odds <strong>{odds_text(row.get('leg1_odds'))}</strong> | Hit prob <strong>{pct(row.get('leg1_probability'))}</strong> | Slot <strong>#{row.get('leg1_lineup_slot', '--')}</strong></div>
                </div>
                <div class="parlay-leg">
                  <div class="label">Leg 2</div>
                  <div class="big">{row.get('leg2_player', '')}</div>
                  <div>{row.get('leg2_team', '')} vs {row.get('leg2_opponent', '')}</div>
                  <div>Odds <strong>{odds_text(row.get('leg2_odds'))}</strong> | Hit prob <strong>{pct(row.get('leg2_probability'))}</strong> | Slot <strong>#{row.get('leg2_lineup_slot', '--')}</strong></div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        why = str(row.get("why_it_has_edge", "") or row.get("why_sharpie_likes_it", "") or "").strip()
        risk = str(row.get("risk_note", "") or row.get("sharpie_concern", "") or "").strip()
        if why:
            st.markdown(f"**Why Sharpie likes it:** {why}")
        if risk:
            st.markdown(f"**What worries Sharpie:** {risk}")

    st.markdown("## Strategy Performance")
    if perf_rows.empty:
        st.info("Parlay strategy performance will appear once the backtest files are published.")
    else:
        cols = st.columns(min(3, len(perf_rows)))
        for idx, (_, rec) in enumerate(perf_rows.iterrows()):
            with cols[idx % len(cols)]:
                st.metric(str(rec.get("Strategy", "")), pct(rec.get("Win Rate")), f"{int(rec.get('Wins', 0))}/{int(rec.get('Sample', 0))} | ROI {pct(rec.get('ROI / 1u'))}")
        display = perf_rows.copy()
        display["Win Rate"] = display["Win Rate"].map(pct)
        display["ROI / 1u"] = display["ROI / 1u"].map(pct)
        display["Avg Odds"] = display["Avg Odds"].map(odds_text)
        st.dataframe(display, use_container_width=True, hide_index=True)


def render_roi_edge_tab() -> None:
    targets, target_label = roi_edge_latest_targets()
    rolling, summary, daily_label = roi_edge_rank_performance()
    st.markdown("## ROI Edge Watchlist")
    st.caption("Shows ROI Edge ranks #1, #3, and #5. Yellow HOLD means the player is not locked yet; green LOCKED means the snapshot is frozen.")

    if targets.empty:
        st.info("No ROI Edge #1/#3/#5 players are available yet. This fills once today's ROI Edge current card is published.")
    else:
        st.markdown(f"<div class='label'>Latest ROI Edge source: {target_label}</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, rank in enumerate([1, 3, 5]):
            rows = targets[targets["display_roi_rank"].eq(rank)]
            with cols[idx]:
                if rows.empty:
                    st.markdown(
                        f"""
                        <div class="roi-card">
                          <div class="roi-rank">ROI Edge Rank #{rank}</div>
                          <div class="big">No Current Player</div>
                          <div style="color:#aab6c5;">This rank is not on the current ROI Edge watchlist.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    continue
                row = rows.iloc[0]
                status = str(row.get("display_roi_status", "HOLD")).upper()
                badge_class = "status-locked" if status == "LOCKED" else "status-hold"
                lineup_status = str(row.get("lineup_status", "") or "")
                reason = row.get("roi_edge_lock_reason", "")
                if status != "LOCKED":
                    reason = f"Hold: {lineup_status or 'not locked yet'}; locks only inside the lock window or after first pitch."
                st.markdown(
                    f"""
                    <div class="roi-card">
                      <div class="roi-rank">ROI Edge Rank #{rank} <span class="status-badge {badge_class}">{status}</span></div>
                      <div class="big">{row.get('player', '')}</div>
                      <div>{row.get('team', '')} vs {row.get('opponent', '')} | DK <strong>{odds_text(row.get('odds'))}</strong></div>
                      <div class="roi-metric-row">
                        <div class="roi-mini"><div class="label">PA Path</div><div class="value">{pct(row.get('pa_path_hit_probability'))}</div></div>
                        <div class="roi-mini"><div class="label">Avg Model</div><div class="value">{pct(row.get('model_prob_avg'))}</div></div>
                        <div class="roi-mini"><div class="label">Edge</div><div class="value">{pct(row.get('avg_model_edge', row.get('edge')))}</div></div>
                      </div>
                      <div style="margin-top:10px;color:#aab6c5;font-size:.92rem;">{reason}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("## Historical Rank Results")
    if summary.empty:
        st.info("ROI Edge rank history is not available yet.")
    else:
        metric_cols = st.columns(3)
        for idx, rank in enumerate([1, 3, 5]):
            row = summary[summary["roi_card_rank"].eq(rank)]
            if row.empty:
                metric_cols[idx].metric(f"Rank #{rank}", "No sample")
                continue
            rec = row.iloc[0]
            metric_cols[idx].metric(
                f"Rank #{rank} All-Time",
                pct(rec.get("hit_rate")),
                f"{int(rec.get('hits', 0))}/{int(rec.get('picks', 0))} | ROI {pct(rec.get('roi'))}",
            )
        st.caption(f"Source: {daily_label}. Recent table below shows the newest resolved ROI Edge rank picks.")
        display_cols = ["date", "roi_card_rank", "player", "team", "opponent", "odds", "pa_path_hit_probability", "actual_hit", "profit"]
        st.dataframe(
            rolling[[col for col in display_cols if col in rolling.columns]].head(60),
            use_container_width=True,
            hide_index=True,
        )


def sharpie_lookup_score(row: pd.Series) -> tuple[float, float, list[str]]:
    model_cols = [
        "model_hit_probability",
        "secondary_hit_probability",
        "third_hit_probability",
        "markov_hit_probability",
        "edgestate_hit_probability",
        "pa_path_hit_probability",
        "swing_hit_probability",
        "bookbias_model_probability",
    ]
    probs = [value(row, col, float("nan")) for col in model_cols]
    probs = [p for p in probs if not pd.isna(p) and 0 < p < 1]
    base = sum(probs) / len(probs) if probs else value(row, "model_hit_probability", 0.60)
    adjustments: list[tuple[str, float]] = []

    if truthy(row.get("confirmed_lineup")):
        adjustments.append(("Confirmed lineup", 0.012))
    else:
        adjustments.append(("Lineup still projected", -0.035))

    slot = int(value(row, "actual_batting_order", value(row, "batting_order", 0)))
    if 1 <= slot <= 3:
        adjustments.append((f"Premium lineup slot #{slot}", 0.010))
    elif 4 <= slot <= 5:
        adjustments.append((f"Strong lineup slot #{slot}", 0.004))
    elif 7 <= slot <= 9:
        adjustments.append((f"Lower-order slot #{slot}", -0.025))

    trust_gap = value(row, "team_trust_gap", 0.0)
    if trust_gap:
        adjustments.append(("Team trust gap", clamp(trust_gap, -0.04, 0.04) * 0.45))
    trust_picks = value(row, "team_trust_picks", 0.0)
    if trust_picks >= 20 and abs(trust_gap) < 0.03:
        adjustments.append(("Team profile has been stable", 0.008))

    pitch_score = value(row, "pitch_mix_matchup_score", 0.0)
    if pitch_score:
        adjustments.append(("Pitch-mix matchup", clamp(pitch_score, -0.04, 0.04) * 0.50))

    bullpen_fatigue = value(row, "opponent_bullpen_fatigue_score", 0.50)
    adjustments.append(("Bullpen fatigue context", clamp(bullpen_fatigue - 0.50, -0.50, 0.50) * 0.018))

    odds_movement = value(row, "odds_movement", 0.0)
    if odds_movement > 0:
        adjustments.append(("Price moved cheaper than open", 0.008))
    elif odds_movement < -25:
        adjustments.append(("Price got more expensive", -0.006))

    pa_value = value(row, "pa_path_relative_value_score", 0.0)
    if pa_value > 25:
        adjustments.append(("PA Path relative value", 0.012))
    elif pa_value < -15:
        adjustments.append(("Weak PA Path relative value", -0.012))

    bookbias = str(row.get("bookbias_recommendation", "")).lower()
    if "avoid" in bookbias or "pass" in bookbias:
        adjustments.append(("BookBias caution", -0.018))
    elif "bet" in bookbias or "watch" in bookbias:
        adjustments.append(("BookBias support", 0.006))

    swing = str(row.get("swing_recommendation", "")).lower()
    if "watch" in swing or "bet" in swing or "b" in swing:
        adjustments.append(("SwingState support", 0.010))

    markov = str(row.get("markov_signal", "")).lower()
    if "upgrade" in markov:
        adjustments.append(("Markov upgrade", 0.010))
    elif "downgrade" in markov:
        adjustments.append(("Markov downgrade", -0.010))

    total_adjustment = sum(delta for _, delta in adjustments)
    score = clamp(base + total_adjustment, 0.10, 0.90)
    drivers = [f"{name}: {delta:+.1%}" for name, delta in adjustments if abs(delta) >= 0.004]
    return score, base, drivers


def sharpie_lean(score: float, row: pd.Series) -> tuple[str, str]:
    odds = value(row, "odds", 0.0)
    implied = value(row, "implied_probability", 0.0)
    edge = score - implied if implied else value(row, "edge", 0.0)
    if score >= 0.68 and edge >= 0.05:
        return "Strong Sharpie Look", "good"
    if score >= 0.63 and edge >= 0.025:
        return "Playable, Price Matters", "warn"
    if odds < -240 and edge < 0.04:
        return "Likely Hit, Price Is Heavy", "warn"
    if score < 0.58 or edge < 0:
        return "Pass / Caution", "bad"
    return "Lean Only", "warn"


def sharpie_performance(picks: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    if picks.empty or results.empty or "actual_hit" not in results.columns:
        return picks.copy()
    if {"allocation", "profit", "roi", "sharpie_rank"}.issubset(results.columns):
        out = results.copy()
        if "pick_date" in out.columns:
            out = out[~out["pick_date"].astype(str).isin(SHARPIE_EXCLUDED_PERFORMANCE_DATES)].copy()
        status = out.get("bet_status", pd.Series("", index=out.index)).astype(str).str.lower()
        rank_num = pd.to_numeric(out.get("sharpie_rank"), errors="coerce")
        out = out[~status.eq("bonus late pick") & rank_num.between(1, 3, inclusive="both")].copy()
        out["actual_hit"] = pd.to_numeric(out.get("actual_hit"), errors="coerce")
        out["allocation"] = pd.to_numeric(out.get("allocation"), errors="coerce")
        out["odds"] = pd.to_numeric(out.get("odds"), errors="coerce")
        out["profit"] = pd.to_numeric(out.get("profit"), errors="coerce")
        out["roi"] = pd.to_numeric(out.get("roi"), errors="coerce")
        return out
    left = picks.copy()
    if "bet_status" in left.columns:
        status = left["bet_status"].astype(str).str.lower()
        left = left[~status.isin(["hold", "bonus late pick"])].copy()
    if "sharpie_rank" in left.columns:
        rank_num = pd.to_numeric(left.get("sharpie_rank"), errors="coerce")
        left = left[rank_num.between(1, 3, inclusive="both")].copy()
    allocation = pd.to_numeric(left.get("allocation", pd.Series(dtype=float)), errors="coerce").fillna(0)
    first_dates = sorted(left.loc[allocation.gt(0), "pick_date"].dropna().astype(str).unique().tolist()) if "pick_date" in left.columns else []
    if len(first_dates) > 1:
        left = left[left["pick_date"].astype(str).ge(first_dates[1])].copy()
    if "pick_date" in left.columns:
        left = left[~left["pick_date"].astype(str).isin(SHARPIE_EXCLUDED_PERFORMANCE_DATES)].copy()
    right = results.copy()
    for frame, date_col in [(left, "pick_date"), (right, "pick_date")]:
        frame["date_key"] = frame.get(date_col, "").astype(str)
        frame["player_key"] = frame.get("player", "").astype(str).str.strip().str.lower()
        frame["team_key"] = frame.get("team", "").astype(str).str.strip()
        frame["opponent_key"] = frame.get("opponent", "").astype(str).str.strip()
    keep = [c for c in ["date_key", "player_key", "team_key", "opponent_key", "actual_hit", "actual_hits"] if c in right.columns]
    merged = left.merge(right[keep], on=["date_key", "player_key", "team_key", "opponent_key"], how="left")
    merged["actual_hit"] = pd.to_numeric(merged.get("actual_hit"), errors="coerce")
    merged["allocation"] = pd.to_numeric(merged.get("allocation"), errors="coerce")
    merged["odds"] = pd.to_numeric(merged.get("odds"), errors="coerce")

    def profit(row: pd.Series) -> float:
        if pd.isna(row.get("actual_hit")) or pd.isna(row.get("allocation")) or pd.isna(row.get("odds")):
            return float("nan")
        if row["actual_hit"] >= 1:
            return row["allocation"] * (row["odds"] / 100 if row["odds"] > 0 else 100 / abs(row["odds"]))
        return -row["allocation"]

    merged["profit"] = merged.apply(profit, axis=1)
    return merged


def rank1_weekday_performance(performance: pd.DataFrame) -> pd.DataFrame:
    columns = ["Day", "Record", "Hit Rate", "Profit", "ROI", "Avg Odds"]
    required = {"pick_date", "sharpie_rank", "actual_hit"}
    if performance.empty or not required.issubset(performance.columns):
        return pd.DataFrame(columns=columns)
    work = performance.copy()
    for column in ["sharpie_rank", "actual_hit", "allocation", "profit", "odds"]:
        work[column] = pd.to_numeric(work.get(column), errors="coerce")
    work["pick_date"] = pd.to_datetime(work["pick_date"], errors="coerce")
    work = work[
        work["sharpie_rank"].eq(1)
        & work["actual_hit"].isin([0, 1])
        & work["allocation"].fillna(0).gt(0)
        & work["pick_date"].notna()
    ].copy()
    if work.empty:
        return pd.DataFrame(columns=columns)
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    work["Day"] = work["pick_date"].dt.day_name()
    summary = (
        work.groupby("Day", observed=True)
        .agg(
            Picks=("actual_hit", "size"),
            Hits=("actual_hit", "sum"),
            **{"Hit Rate": ("actual_hit", "mean"), "Staked": ("allocation", "sum"), "Profit": ("profit", "sum"), "Avg Odds": ("odds", "mean")},
        )
        .reindex(order)
        .dropna(subset=["Picks"])
        .reset_index()
    )
    summary["Picks"] = summary["Picks"].astype(int)
    summary["Hits"] = summary["Hits"].astype(int)
    summary["Record"] = summary["Hits"].astype(str) + "-" + (summary["Picks"] - summary["Hits"]).astype(str)
    summary["ROI"] = summary["Profit"] / summary["Staked"].replace(0, pd.NA)
    return summary[columns]


def previous_card_reflection(perf: pd.DataFrame, run_date: str) -> dict[str, object]:
    if perf.empty or "actual_hit" not in perf.columns or "pick_date" not in perf.columns:
        return {
            "has_reflection": False,
            "summary": "Sharpie does not have a resolved prior card to review yet.",
            "lesson": "Once yesterday's results are published, this section will explain what the card taught him.",
            "rows": pd.DataFrame(),
        }

    work = perf.copy()
    work["pick_date"] = work["pick_date"].astype(str)
    for column in ["actual_hit", "allocation", "profit", "sharpie_rank", "sharpie_probability", "sharpie_ev_per_dollar"]:
        if column in work.columns:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    status = work.get("bet_status", pd.Series("", index=work.index)).astype(str).str.lower()
    work = work[
        work["actual_hit"].isin([0, 1])
        & work.get("allocation", pd.Series(0, index=work.index)).fillna(0).gt(0)
        & work.get("sharpie_rank", pd.Series(99, index=work.index)).between(1, 3, inclusive="both")
        & ~status.isin(["hold", "bonus late pick"])
        & work["pick_date"].lt(str(run_date))
    ].copy()
    if work.empty:
        return {
            "has_reflection": False,
            "summary": "No prior Sharpie card has resolved before today's slate.",
            "lesson": "Sharpie is still waiting for a prior card to judge against hit rate, profit, and ROI.",
            "rows": pd.DataFrame(),
        }

    try:
        target_date = (dt.date.fromisoformat(str(run_date)) - dt.timedelta(days=1)).isoformat()
    except ValueError:
        target_date = ""
    review_date = target_date if target_date in set(work["pick_date"]) else work["pick_date"].sort_values().iloc[-1]
    card_rows = work[work["pick_date"].eq(review_date)].sort_values("sharpie_rank").copy()
    picks_count = len(card_rows)
    hits = int(card_rows["actual_hit"].sum())
    staked = float(card_rows["allocation"].sum())
    profit_value = float(card_rows["profit"].sum())
    hit_rate = hits / picks_count if picks_count else 0.0
    roi = profit_value / staked if staked else 0.0

    hit_names = card_rows[card_rows["actual_hit"].eq(1)]["player"].astype(str).tolist()
    miss_names = card_rows[card_rows["actual_hit"].eq(0)]["player"].astype(str).tolist()
    biggest = card_rows.sort_values("allocation", ascending=False).iloc[0] if not card_rows.empty else pd.Series(dtype=object)
    biggest_result = "hit" if float(biggest.get("actual_hit", 0) or 0) >= 1 else "missed"

    summary = (
        f"{review_date}: Sharpie went {hits}/{picks_count} ({hit_rate:.1%}) for {money(profit_value)} "
        f"on {money(staked)} staked ({roi:.1%} ROI)."
    )
    if hit_names:
        summary += f" Hits: {', '.join(hit_names)}."
    if miss_names:
        summary += f" Misses: {', '.join(miss_names)}."

    if profit_value > 0 and biggest_result == "hit":
        lesson = (
            f"The main sizing call worked: {biggest.get('player', '')} was the largest allocation and got there. "
            "Sharpie should keep rewarding this profile when model agreement, lineup opportunity, and price all line up."
        )
    elif profit_value > 0:
        lesson = "The card still made money, but the largest bet did not carry it. That argues for selective diversification when the top edge is not clearly separated."
    elif biggest_result == "missed":
        lesson = (
            "The largest allocation missed. Sharpie should be stricter before concentrating exposure and demand cleaner agreement, price, and player reliability."
        )
    else:
        lesson = "The hit calls were not enough to overcome price or sizing. Sharpie should prioritize profit per dollar over raw hit likelihood."

    reads: list[str] = []
    for _, row in card_rows.iterrows():
        player = str(row.get("player", "This pick"))
        result = "hit" if float(row.get("actual_hit", 0) or 0) >= 1 else "missed"
        line = (
            f"{player} {result}: {money(row.get('allocation'))} at {odds_text(row.get('odds'))}, "
            f"Sharpie probability {pct(row.get('sharpie_probability'))}, EV/$ {pct(row.get('sharpie_ev_per_dollar'))}."
        )
        like = str(row.get("what_sharpie_likes", "") or "").strip()
        concern = str(row.get("sharpie_concern", "") or "").strip()
        if result == "hit" and like:
            line += f" What was right: {like}"
        elif result == "missed" and concern:
            line += f" Warning sign: {concern}"
        reads.append(line)

    card_rows["reflection_read"] = reads
    return {
        "has_reflection": True,
        "review_date": review_date,
        "picks": picks_count,
        "hits": hits,
        "staked": staked,
        "profit": profit_value,
        "roi": roi,
        "hit_rate": hit_rate,
        "summary": summary,
        "lesson": lesson,
        "diagnostics": reads,
        "rows": card_rows,
    }


picks = refresh_game_timing(read_csv(SHARPIE_PICKS))
writeups = read_csv(SHARPIE_WRITEUPS)
results = read_csv(SHARPIE_RESULTS_PUBLIC)
lookup = read_csv(PLAYER_LOOKUP)
sol_latest = read_json(SHARPIE_SOL_LATEST)

date_candidates = [latest_date(picks, "pick_date")]
if not lookup.empty:
    date_candidates.append(latest_date(lookup, "lookup_date"))
run_date = max([str(item) for item in date_candidates if str(item).strip()], default=dt.date.today().isoformat())
today = picks[picks.get("pick_date", pd.Series(dtype=str)).astype(str).eq(str(run_date))].copy() if not picks.empty else pd.DataFrame()
today = today.sort_values("sharpie_rank") if "sharpie_rank" in today.columns else today
perf = sharpie_performance(picks, results)
resolved = perf[pd.to_numeric(perf.get("actual_hit", pd.Series(dtype=float)), errors="coerce").isin([0, 1])].copy() if not perf.empty else pd.DataFrame()

st.markdown(
    f"""
    <div class="sharpie-stage">
      <div class="sharpie-logo">Sharpie</div>
      <div class="sharpie-tagline">Stats. Trends. Edges.</div>
      <div class="sharpie-date">Latest card date: <span class="accent">{run_date}</span></div>
      <div class="sharpie-character" aria-label="Animated Sharpie mascot">
        <div class="sharpie-pencil"></div>
        <div class="sharpie-cap"><span>Sharpie</span></div>
        <div class="sharpie-head">
          <div class="sharpie-eye left"></div>
          <div class="sharpie-eye right"></div>
          <div class="sharpie-smile"></div>
          <div class="sharpie-beard"></div>
        </div>
        <div class="sharpie-body"></div>
        <div class="sharpie-chain"></div>
        <div class="sharpie-phone"></div>
        <div class="sharpie-slip"></div>
      </div>
      <div class="sharpie-bubbles">
        <div class="sharpie-bubble"><strong>I don't guess.</strong><br>I calculate the card.</div>
        <div class="sharpie-bubble"><strong>Profit first.</strong><br>0-3 picks. Cash can stay on the bench.</div>
        <div class="sharpie-bubble"><strong>Today:</strong><br>Green locked bets count. Gold holds are watchlist only.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Informational model output only. Betting involves risk. Odds and lineups can move after this card is published.")

sharpie_tab, parlay_tab, roi_tab = st.tabs(["Sharpie's Top 3", "Best Parlay", "Locked ROI Edge"])

with sharpie_tab:
    if today.empty:
        st.warning("Sharpie has not published a card yet for the latest available date.")
    else:
        status = today.get("bet_status", pd.Series("Locked", index=today.index)).fillna("Locked").astype(str)
        locked_today = today[~status.str.lower().eq("hold")].copy()
        hold_today = today[status.str.lower().eq("hold")].copy()
        allocated = pd.to_numeric(locked_today.get("allocation", pd.Series(dtype=float)), errors="coerce").sum()
        reserved = pd.to_numeric(hold_today.get("reserved_allocation", pd.Series(dtype=float)), errors="coerce").sum()
        cash_held = pd.to_numeric(today.get("sharpie_cash_held", pd.Series(dtype=float)), errors="coerce").max()
        expected_profit = pd.to_numeric(locked_today.get("sharpie_expected_profit", pd.Series(dtype=float)), errors="coerce").sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="card"><div class="label">Locked / Holds</div><div class="big">{len(locked_today)} / {len(hold_today)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="card"><div class="label">Allocated</div><div class="big">{money(allocated)}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="card"><div class="label">Reserved / Cash</div><div class="big">{money(reserved)} / {money(cash_held)}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="card"><div class="label">Projected EV</div><div class="big good">{money(expected_profit)}</div></div>', unsafe_allow_html=True)

        sol_precision = sol_latest.get("precision_hybrid_card", {}) if isinstance(sol_latest, dict) else {}
        sol_allocation = sol_latest.get("allocation_sol", {}).get("all", {}) if isinstance(sol_latest, dict) else {}
        if sol_latest:
            st.markdown("## Sol Precision Layer")
            st.caption(
                "Sol is Sharpie's independent walk-forward support model. It helps choose the second core play, "
                "admits a third only when qualified, and applies price-aware sizing with a hard DraftKings ceiling of -265."
            )
            sol_profit = float(sol_allocation.get("profit", 0) or 0)
            sol_initial_bankroll = float(sol_allocation.get("initial_bankroll", 100) or 100)
            sol_ending_bankroll = float(sol_allocation.get("ending_bankroll", sol_initial_bankroll + sol_profit) or 0)
            sol_running_return = float(
                sol_allocation.get(
                    "return_on_initial_bankroll",
                    sol_profit / sol_initial_bankroll if sol_initial_bankroll else 0,
                )
                or 0
            )
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Validated Hit Rate", pct(sol_precision.get("hit_rate")), f"{int(sol_precision.get('picks', 0) or 0)} picks")
            sc2.metric("$100 Test Bankroll", money(sol_ending_bankroll), f"{money(sol_profit)} profit")
            sc3.metric("Running ROI", pct(sol_running_return), "Return on initial $100")
            sc4.metric("Turnover ROI", pct(sol_allocation.get("roi")), f"{money(sol_allocation.get('stake'))} wagered")
            sc5.metric("Card Rule", "2 Core + 1", "Qualified third only")
            st.caption(
                f"Research snapshot: {sol_latest.get('as_of', '--')}. Running ROI uses the initial $100 as its denominator; "
                "turnover ROI uses all recycled wagers. Stake sizes remain the tested fixed-dollar amounts rather than compounding upward."
            )

        reflection = previous_card_reflection(perf, str(run_date))
        st.markdown("## Sharpie's Previous Card Reflection")
        if not reflection.get("has_reflection"):
            st.info(str(reflection.get("summary", "Sharpie does not have a resolved prior card to review yet.")))
            st.caption(str(reflection.get("lesson", "Once results are published, Sharpie will explain what worked and what he learned.")))
        else:
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Reviewed Card", str(reflection.get("review_date", "--")))
            r2.metric("Hit Rate", f"{int(reflection.get('hits', 0))}/{int(reflection.get('picks', 0))}", pct(reflection.get("hit_rate")))
            r3.metric("Profit", money(reflection.get("profit")), f"{pct(reflection.get('roi'))} ROI")
            r4.metric("Stake", money(reflection.get("staked")), "Official picks")
            st.markdown(f"**What happened:** {reflection.get('summary', '')}")
            st.markdown(f"**What Sharpie learned:** {reflection.get('lesson', '')}")
            diagnostics = reflection.get("diagnostics", [])
            if diagnostics:
                with st.expander("Pick-by-pick reflection", expanded=True):
                    for read in diagnostics:
                        st.markdown(f"- {read}")
            reflection_rows = reflection.get("rows", pd.DataFrame())
            if isinstance(reflection_rows, pd.DataFrame) and not reflection_rows.empty:
                with st.expander("Reflection data table", expanded=False):
                    show_cols = [
                        "sharpie_rank",
                        "player",
                        "team",
                        "opponent",
                        "odds",
                        "allocation",
                        "actual_hit",
                        "actual_hits",
                        "profit",
                        "sharpie_ev_per_dollar",
                        "sharpie_allocation_reason",
                        "sharpie_concern",
                    ]
                    st.dataframe(reflection_rows[[col for col in show_cols if col in reflection_rows.columns]], use_container_width=True, hide_index=True)

        st.markdown(
            """
            <div class="status-explainer">
              <strong><span class="status-badge status-locked">LOCKED</span></strong>
              means Sharpie has committed real bankroll and this pick is tracked.
              <br>
              <strong><span class="status-badge status-hold">HOLD</span></strong>
              means watchlist only: no bet is committed, the player can still be dropped, and the shown reserve is only planned exposure if conditions improve.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## Today's Sharpie Card")
        for _, row in locked_today.iterrows():
            sol_badge = '<span class="sol-badge">SOL SUPPORT</span>' if truthy(row.get("sharpie_sol_used")) else ""
            sol_risk_badge = '<span class="sol-badge sol-risk-badge">SOL RISK WATCH</span>' if truthy(row.get("sharpie_sol_lead_risk_warning")) else ""
            gold_star_badge = '<span class="sol-badge" style="border-color:#ffd24a;color:#ffd24a;background:rgba(255,210,74,.14);">&#9733; GOLD STAR</span>' if truthy(row.get("sharpie_rank1_gold_star")) else ""
            streak_warning_badge = '<span class="sol-badge" style="border-color:#ff6b57;color:#ff9a88;background:rgba(255,75,65,.20);">STREAK WARNING</span>' if truthy(row.get("sharpie_rank1_streak_warning")) else ""
            st.markdown(
                f"""
                <div class="pick locked">
                  <div class="label">#{int(float(row.get('sharpie_rank', 0) or 0))} | {row.get('team', '')} vs {row.get('opponent', '')}</div>
                  <div class="big">{row.get('player', '')}{gold_star_badge}{streak_warning_badge} <span class="accent">{money(row.get('allocation'))}</span><span class="status-badge status-locked">LOCKED</span>{sol_badge}{sol_risk_badge}</div>
                  <div>Bet committed: <strong>{money(row.get('allocation'))}</strong> | Odds: <strong>{row.get('odds', '--')}</strong> | Probability: <strong>{pct(row.get('sharpie_probability'))}</strong> | EV/$: <strong>{pct(row.get('sharpie_ev_per_dollar'))}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if str(row.get("lock_rule", "")).strip():
                st.markdown(f"**Lock rule:** {row.get('lock_rule', '')}")
            if pd.notna(row.get("sharpie_sol_rank")) or pd.notna(row.get("sharpie_sol_probability")):
                sol_rank = f"#{int(value(row, 'sharpie_sol_rank', 0))}" if value(row, "sharpie_sol_rank", 0) else "--"
                sol_tier = str(row.get("sharpie_sol_support_tier", "") or "").strip()
                st.markdown(
                    f"**Sol read:** rank {sol_rank} at {pct(row.get('sharpie_sol_probability'))}"
                    f"{f' | tier {sol_tier}' if sol_tier else ''}. {row.get('sharpie_sol_note', '')}"
                )
            if str(row.get("sharpie_sol_allocation_note", "") or "").strip():
                st.markdown(f"**Sol sizing input:** {row.get('sharpie_sol_allocation_note', '')}")
            if truthy(row.get("sharpie_rank1_gold_star")):
                st.markdown(f"**Gold Star filter:** {row.get('sharpie_rank1_gold_star_note', '')}")
            if truthy(row.get("sharpie_rank1_streak_warning")):
                st.error(str(row.get("sharpie_rank1_streak_warning_note", "")))
            st.markdown(f"**Why this amount:** {row.get('sharpie_allocation_reason', '')}")
            st.markdown(f"**Why Sharpie likes it:** {row.get('what_sharpie_likes', '')}")
            st.markdown(f"**Main concern:** {row.get('sharpie_concern', '')}")
            if str(row.get("sharpie_team_context", "")).strip():
                st.markdown(f"**Team context:** {row.get('sharpie_team_context', '')}")
            st.divider()
        if not hold_today.empty:
            st.markdown("## Hold Spots")
            for _, row in hold_today.iterrows():
                sol_badge = '<span class="sol-badge">SOL SUPPORT</span>' if truthy(row.get("sharpie_sol_used")) else ""
                sol_risk_badge = '<span class="sol-badge sol-risk-badge">SOL RISK WATCH</span>' if truthy(row.get("sharpie_sol_lead_risk_warning")) else ""
                gold_star_badge = '<span class="sol-badge" style="border-color:#ffd24a;color:#ffd24a;background:rgba(255,210,74,.14);">&#9733; GOLD STAR</span>' if truthy(row.get("sharpie_rank1_gold_star")) else ""
                streak_warning_badge = '<span class="sol-badge" style="border-color:#ff6b57;color:#ff9a88;background:rgba(255,75,65,.20);">STREAK WARNING</span>' if truthy(row.get("sharpie_rank1_streak_warning")) else ""
                st.markdown(
                    f"""
                    <div class="hold-card">
                      <div class="label">#{int(float(row.get('sharpie_rank', 0) or 0))} | HOLD | {row.get('team', '')} vs {row.get('opponent', '')}</div>
                      <div class="big">{row.get('player', '')}{gold_star_badge}{streak_warning_badge} <span class="money-muted">$0 bet committed</span><span class="status-badge status-hold">HOLD</span>{sol_badge}{sol_risk_badge}</div>
                      <div>Reserved if conditions improve: <strong class="warn">{money(row.get('reserved_allocation'))}</strong> | Current odds: <strong>{row.get('current_snapshot_odds', row.get('odds', '--'))}</strong> | Projected probability: <strong>{pct(row.get('sharpie_probability'))}</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if str(row.get("lock_rule", "")).strip():
                    st.markdown(f"**Hold status:** {row.get('lock_rule', '')}")
                if pd.notna(row.get("sharpie_sol_rank")) or pd.notna(row.get("sharpie_sol_probability")):
                    sol_rank = f"#{int(value(row, 'sharpie_sol_rank', 0))}" if value(row, "sharpie_sol_rank", 0) else "--"
                    st.markdown(
                        f"**Sol read:** rank {sol_rank} at {pct(row.get('sharpie_sol_probability'))}. "
                        f"{row.get('sharpie_sol_note', '')}"
                    )
                if truthy(row.get("sharpie_rank1_gold_star")):
                    st.markdown(f"**Gold Star filter:** {row.get('sharpie_rank1_gold_star_note', '')}")
                if truthy(row.get("sharpie_rank1_streak_warning")):
                    st.error(str(row.get("sharpie_rank1_streak_warning_note", "")))
                st.markdown(f"**Trigger:** {row.get('hold_trigger', '')}")
                st.markdown(f"**Why hold it:** {row.get('sharpie_allocation_reason', '')}")
                st.divider()

        st.markdown("## Late Hitter Buyback Watch")
        st.caption("Live-bet reference only: if one of these hitters misses his first PA, compare DraftKings live odds to Sharpie's fair after-0-for-1 line.")
        buyback = live_buyback_board(str(run_date))
        if buyback.empty:
            st.info("No Late Hitter buyback reserve slots are available yet. This board fills from the top 30 after the buyback model runs.")
        else:
            source_updated = str(buyback.get("_source_updated_at", pd.Series("", index=buyback.index)).iloc[0] or "")
            locked_count = (
                int(buyback["late_hitter_lock_status"].astype(str).str.upper().eq("LOCKED").sum())
                if "late_hitter_lock_status" in buyback.columns
                else 0
            )
            hold_count = len(buyback) - locked_count
            metric_cols = st.columns(3)
            metric_cols[0].markdown(f'<div class="card"><div class="label">Buyback Watch</div><div class="big">{len(buyback)}</div><div>{locked_count} locked / {hold_count} hold</div></div>', unsafe_allow_html=True)
            metric_cols[1].markdown(f'<div class="card"><div class="label">Avg After 0-for-1</div><div class="big">{pct(buyback.get("bayes_recovery_hit_rate", pd.Series(dtype=float)).mean())}</div></div>', unsafe_allow_html=True)
            metric_cols[2].markdown(f'<div class="card"><div class="label">Avg Fair Live Odds</div><div class="big">{odds_text(buyback.get("fair_live_odds_after_0for1", pd.Series(dtype=float)).mean())}</div></div>', unsafe_allow_html=True)
            if source_updated:
                st.markdown(f"<div class='label'>Late Hitter file updated: <span class='accent'>{source_updated}</span></div>", unsafe_allow_html=True)
            for rank, (_, row) in enumerate(buyback.iterrows(), start=1):
                display_rank = row.get("sharpie_late_hitter_slot", rank)
                try:
                    display_rank = int(float(display_rank))
                except (TypeError, ValueError):
                    display_rank = rank
                current_odds = row.get("current_dk_hit_odds", row.get("odds"))
                fair_live = row.get("fair_live_odds_after_0for1")
                lock_status = str(row.get("late_hitter_lock_status", "LOCKED") or "LOCKED").upper()
                badge_class = "status-locked" if lock_status == "LOCKED" else "status-hold"
                slot = row.get("today_lineup_slot", row.get("avg_lineup_slot"))
                slot_text = f"#{int(float(slot))}" if pd.notna(slot) else "--"
                move = row.get("pregame_to_0for1_fair_odds_move")
                move_text = f"{float(move):+.0f} cents" if pd.notna(move) else "--"
                remaining = row.get("avg_remaining_pa_after_0for1")
                remaining_text = f"{float(remaining):.1f}" if pd.notna(remaining) else "--"
                samples = row.get("first_pa_no_hit_games")
                samples_text = f"{int(float(samples))}" if pd.notna(samples) else "--"
                st.markdown(
                    f"""
                    <div class="hold-card">
                      <div class="label">Late Hitter #{display_rank} | {row.get('team', row.get('team_last', ''))} vs {row.get('opponent', '--')} | Slot {slot_text}</div>
                      <div class="big">{row.get('player', '')} <span class="accent">Fair after 0-for-1: {odds_text(fair_live)}</span><span class="status-badge {badge_class}">{lock_status}</span></div>
                      <div>Current DK: <strong>{odds_text(current_odds)}</strong> | After 0-for-1 hit: <strong>{pct(row.get('bayes_recovery_hit_rate'))}</strong> | Raw recovery: <strong>{pct(row.get('recovery_hit_rate_after_0for1'))}</strong></div>
                      <div style="color:#aab6c5;margin-top:6px;">Samples: {samples_text} | Avg remaining PA: {remaining_text} | Expected price move: {move_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if str(row.get("late_hitter_lock_note", "")).strip():
                    st.markdown(f"**Lineup lock:** {row.get('late_hitter_lock_note', '')}")
                st.markdown(f"**Sharpie live trigger:** If DK is better than **{odds_text(fair_live)}** after the first miss, this becomes a live-bet candidate.")
                st.divider()

with roi_tab:
    render_roi_edge_tab()

with parlay_tab:
    render_best_parlay_tab(str(run_date))

st.markdown("## Ask Sharpie About A Batter")
st.caption("Search today's public player board by last name or full name. Sharpie's score blends the models with lineup, team trust, matchup, PA path, market, and form context.")
if lookup.empty:
    st.info("Today's batter lookup file has not been published yet.")
else:
    latest_lookup_date = latest_date(lookup, "lookup_date")
    lookup_today = lookup[lookup.get("lookup_date", pd.Series(dtype=str)).astype(str).eq(str(latest_lookup_date))].copy()
    if lookup_today.empty:
        lookup_today = lookup.copy()
    query = st.text_input("Batter name", placeholder="Example: Judge, Ohtani, Tatis")
    if query.strip():
        needle = query.strip().lower()
        names = lookup_today.get("player", pd.Series(dtype=str)).astype(str).str.lower()
        matches = lookup_today[names.str.contains(needle, na=False)].copy()
        if matches.empty:
            st.warning("Sharpie could not find that player on today's board. Try a shorter last-name search.")
        else:
            matches = matches.sort_values(["confirmed_lineup", "player"], ascending=[False, True]).reset_index(drop=True)
            labels = []
            for idx, row in matches.iterrows():
                lineup = "confirmed" if truthy(row.get("confirmed_lineup")) else str(row.get("lineup_status", "projected") or "projected")
                labels.append(
                    f"{row.get('player', '')} | {row.get('team', '')} vs {row.get('opponent', '')} | "
                    f"DK {odds_text(row.get('odds'))} | {lineup}"
                )
            selected_label = st.selectbox("Select the batter", labels)
            selected = matches.iloc[labels.index(selected_label)]
            sharpie_score, model_blend, drivers = sharpie_lookup_score(selected)
            lean, lean_class = sharpie_lean(sharpie_score, selected)
            implied = value(selected, "implied_probability", 0.0)
            sharpie_edge = sharpie_score - implied if implied else float("nan")

            st.markdown(
                f"""
                <div class="pick">
                  <div class="label">{selected.get('team', '')} vs {selected.get('opponent', '')} | Opposing pitcher: {selected.get('opposing_pitcher', '--')}</div>
                  <div class="big">{selected.get('player', '')} <span class="{lean_class}">{pct(sharpie_score)}</span></div>
                  <div>DraftKings odds: <strong>{odds_text(selected.get('odds'))}</strong> | Sharpie read: <strong class="{lean_class}">{lean}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Sharpie Probability", pct(sharpie_score))
            s2.metric("Model Blend", pct(model_blend))
            s3.metric("Market Implied", pct(implied))
            s4.metric("Sharpie Edge", pct(sharpie_edge))

            lineup_slot = int(value(selected, "actual_batting_order", value(selected, "batting_order", 0)))
            projected_pa = value(selected, "actual_projected_pa", value(selected, "projected_pa", 0.0))
            team_gap = value(selected, "team_trust_gap", 0.0)
            trust_hit_rate = value(selected, "team_trust_hit_rate", float("nan"))
            pitch_score = value(selected, "pitch_mix_matchup_score", 0.0)
            pa_value = value(selected, "pa_path_relative_value_score", 0.0)
            odds_move = value(selected, "odds_movement", 0.0)
            player_sample = value(selected, "player_history_sample", 0.0)
            player_gap = value(selected, "player_history_gap", 0.0)

            st.markdown("### Sharpie's Notes")
            n1, n2 = st.columns(2)
            with n1:
                st.markdown(
                    f"""
                    - **Lineup:** slot #{lineup_slot or '--'}, {projected_pa:.2f} projected PA, {selected.get('lineup_status', '--')}
                    - **Team trust:** {pct(trust_hit_rate)} hit rate, trust gap {team_gap:+.1%}
                    - **Player history:** {player_sample:.0f} samples, model gap {player_gap:+.1%}
                    - **Pitch mix:** {selected.get('pitch_mix_primary_pitch', '--')} profile, score {pitch_score:+.3f}
                    - **PA Path:** relative score {pa_value:+.1f}, rank {selected.get('pa_path_relative_rank', '--')}
                    """
                )
            with n2:
                st.markdown(
                    f"""
                    - **Market:** open {odds_text(selected.get('opening_odds'))}, current {odds_text(selected.get('odds'))}, move {odds_move:+.0f}
                    - **BookBias:** {selected.get('bookbias_recommendation', '--')}
                    - **SwingState:** {selected.get('swing_recommendation', '--')}
                    - **Regime:** {selected.get('markov_signal', '--')} / {selected.get('edgestate_signal', '--')}
                    """
                )
            if drivers:
                st.markdown("**What moved Sharpie's score away from the raw model blend:** " + "; ".join(drivers[:8]))
            key_reason = str(selected.get("bookbias_key_reason", "") or selected.get("swing_key_reason", "") or "").strip()
            if key_reason:
                st.markdown(f"**Extra read:** {key_reason}")
    else:
        st.info("Type a batter name above and Sharpie will pull up today's DraftKings price and his adjusted read.")

if not writeups.empty:
    writeup_today = writeups[writeups.get("writeup_date", pd.Series(dtype=str)).astype(str).eq(str(run_date))].copy()
    if not writeup_today.empty:
        latest = writeup_today.tail(1).iloc[0]
        st.markdown("## Sharpie's Read")
        st.markdown(f"**Headline:** {latest.get('headline', '')}")
        st.markdown(f"**Model read:** {latest.get('model_performance_read', '')}")
        st.markdown(f"**Performance trends:** {latest.get('performance_trends', '')}")
        st.markdown(f"**Takeaway:** {latest.get('sharpie_takeaway', '')}")
        st.markdown(f"**Risk note:** {latest.get('risk_note', '')}")

st.markdown("<div class='tracked-performance-title'><h2>Tracked Performance</h2></div>", unsafe_allow_html=True)
if resolved.empty:
    st.info("Resolved Sharpie results will appear here after games are graded.")
else:
    hit_rate = resolved["actual_hit"].mean()
    profit = pd.to_numeric(resolved.get("profit"), errors="coerce").sum()
    staked = pd.to_numeric(resolved.get("allocation"), errors="coerce").sum()
    roi = profit / staked if staked else float("nan")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Resolved Bets", f"{len(resolved):,}")
    p2.metric("Hit Rate", pct(hit_rate))
    p3.metric("Profit", money(profit))
    p4.metric("ROI", pct(roi))
    st.markdown("### #1 Pick Performance By Weekday")
    st.caption("Running resolved results for Sharpie's lead pick; unresolved games and excluded dates are omitted.")
    weekday_rank1 = rank1_weekday_performance(resolved)
    if weekday_rank1.empty:
        st.info("Weekday results will populate after number-one picks resolve.")
    else:
        weekday_display = weekday_rank1.copy()
        weekday_display["Hit Rate"] = weekday_display["Hit Rate"].map(lambda value: f"{value:.1%}")
        weekday_display["Profit"] = weekday_display["Profit"].map(money)
        weekday_display["ROI"] = weekday_display["ROI"].map(pct)
        weekday_display["Avg Odds"] = weekday_display["Avg Odds"].map(lambda value: f"{value:+.0f}")
        st.dataframe(weekday_display, use_container_width=True, hide_index=True)
    show_cols = [
        "pick_date",
        "sharpie_rank",
        "player",
        "team",
        "opponent",
        "odds",
        "allocation",
        "actual_hit",
        "actual_hits",
        "profit",
        "roi",
    ]
    st.dataframe(resolved[[c for c in show_cols if c in resolved.columns]].sort_values(["pick_date", "sharpie_rank"], ascending=[False, True]), use_container_width=True, hide_index=True)
