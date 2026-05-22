from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
SHARPIE_PICKS = ROOT / "data" / "processed" / "sharpie_picks.csv"
SHARPIE_WRITEUPS = ROOT / "data" / "processed" / "sharpie_writeups.csv"
SHARPIE_RESULTS_PUBLIC = ROOT / "data" / "processed" / "sharpie_results_public.csv"


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
    .label { color: #aab6c5; font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }
    .big { font-size: 1.9rem; font-weight: 900; }
    .accent { color: #ffbf3f; }
    .good { color: #62d26f; }
    .warn { color: #ffbf3f; }
    .bad { color: #ff5b6b; }
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
    return pd.read_csv(path)


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


def sharpie_performance(picks: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    if picks.empty or results.empty or "actual_hit" not in results.columns:
        return picks.copy()
    left = picks.copy()
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


picks = read_csv(SHARPIE_PICKS)
writeups = read_csv(SHARPIE_WRITEUPS)
results = read_csv(SHARPIE_RESULTS_PUBLIC)

run_date = latest_date(picks, "pick_date")
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
        <div class="sharpie-bubble"><strong>Today:</strong><br>Watching odds, lineups, model agreement, and ROI.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Informational model output only. Betting involves risk. Odds and lineups can move after this card is published.")

if today.empty:
    st.warning("Sharpie has not published a card yet for the latest available date.")
else:
    allocated = pd.to_numeric(today.get("allocation", pd.Series(dtype=float)), errors="coerce").sum()
    cash_held = pd.to_numeric(today.get("sharpie_cash_held", pd.Series(dtype=float)), errors="coerce").max()
    expected_profit = pd.to_numeric(today.get("sharpie_expected_profit", pd.Series(dtype=float)), errors="coerce").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="card"><div class="label">Picks</div><div class="big">{len(today)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><div class="label">Allocated</div><div class="big">{money(allocated)}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card"><div class="label">Cash Held</div><div class="big">{money(cash_held)}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card"><div class="label">Projected EV</div><div class="big good">{money(expected_profit)}</div></div>', unsafe_allow_html=True)

    st.markdown("## Today's Sharpie Card")
    for _, row in today.iterrows():
        st.markdown(
            f"""
            <div class="pick">
              <div class="label">#{int(float(row.get('sharpie_rank', 0) or 0))} | {row.get('team', '')} vs {row.get('opponent', '')}</div>
              <div class="big">{row.get('player', '')} <span class="accent">{money(row.get('allocation'))}</span></div>
              <div>Odds: <strong>{row.get('odds', '--')}</strong> | Probability: <strong>{pct(row.get('sharpie_probability'))}</strong> | EV/$: <strong>{pct(row.get('sharpie_ev_per_dollar'))}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"**Why this amount:** {row.get('sharpie_allocation_reason', '')}")
        st.markdown(f"**Why Sharpie likes it:** {row.get('what_sharpie_likes', '')}")
        st.markdown(f"**Main concern:** {row.get('sharpie_concern', '')}")
        if str(row.get("sharpie_team_context", "")).strip():
            st.markdown(f"**Team context:** {row.get('sharpie_team_context', '')}")
        st.divider()

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

st.markdown("## Tracked Performance")
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
    ]
    st.dataframe(resolved[[c for c in show_cols if c in resolved.columns]].sort_values(["pick_date", "sharpie_rank"], ascending=[False, True]), use_container_width=True, hide_index=True)
