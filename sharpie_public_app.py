from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
SHARPIE_PICKS = ROOT / "data" / "processed" / "sharpie_picks.csv"
SHARPIE_WRITEUPS = ROOT / "data" / "processed" / "sharpie_writeups.csv"
SHARPIE_RESULTS_PUBLIC = ROOT / "data" / "processed" / "sharpie_results_public.csv"
PLAYER_LOOKUP = ROOT / "data" / "processed" / "sharpie_player_lookup_public.csv"
SHARPIE_EXCLUDED_PERFORMANCE_DATES = {"2026-05-23"}


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
        out["actual_hit"] = pd.to_numeric(out.get("actual_hit"), errors="coerce")
        out["allocation"] = pd.to_numeric(out.get("allocation"), errors="coerce")
        out["odds"] = pd.to_numeric(out.get("odds"), errors="coerce")
        out["profit"] = pd.to_numeric(out.get("profit"), errors="coerce")
        out["roi"] = pd.to_numeric(out.get("roi"), errors="coerce")
        return out
    left = picks.copy()
    if "bet_status" in left.columns:
        left = left[~left["bet_status"].astype(str).str.lower().eq("hold")].copy()
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


picks = read_csv(SHARPIE_PICKS)
writeups = read_csv(SHARPIE_WRITEUPS)
results = read_csv(SHARPIE_RESULTS_PUBLIC)
lookup = read_csv(PLAYER_LOOKUP)

run_date = latest_date(picks, "pick_date")
if (not lookup.empty) and (picks.empty or run_date == dt.date.today().isoformat()):
    run_date = latest_date(lookup, "lookup_date")
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

    st.markdown("## Today's Sharpie Card")
    for _, row in locked_today.iterrows():
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
    if not hold_today.empty:
        st.markdown("## Hold Spots")
        for _, row in hold_today.iterrows():
            st.markdown(
                f"""
                <div class="card">
                  <div class="label">#{int(float(row.get('sharpie_rank', 0) or 0))} | HOLD | {row.get('team', '')} vs {row.get('opponent', '')}</div>
                  <div class="big">{row.get('player', '')} <span class="warn">{money(row.get('reserved_allocation'))}</span></div>
                  <div>Odds: <strong>{row.get('odds', '--')}</strong> | Projected probability: <strong>{pct(row.get('sharpie_probability'))}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"**Trigger:** {row.get('hold_trigger', '')}")
            st.markdown(f"**Why hold it:** {row.get('sharpie_allocation_reason', '')}")
            st.divider()

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
        "roi",
    ]
    st.dataframe(resolved[[c for c in show_cols if c in resolved.columns]].sort_values(["pick_date", "sharpie_rank"], ascending=[False, True]), use_container_width=True, hide_index=True)
