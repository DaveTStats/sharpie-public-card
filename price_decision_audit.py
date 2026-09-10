"""Prospective decision snapshots. Never treat recorded prices as filled wagers."""
import datetime as dt
import hashlib
from pathlib import Path

import pandas as pd

VERSION = "price-decision-v1"


def read(path):
    try:
        return pd.read_csv(path, low_memory=False)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def number(value):
    return pd.to_numeric(value, errors="coerce")


def price_metrics(probability, odds):
    p, odds = number(probability), number(odds)
    if pd.isna(p) or not 0 < p < 1 or pd.isna(odds) or abs(odds) < 100:
        return {}
    conservative = max(.01, p - .03)
    decimal = 1 + (100 / -odds if odds < 0 else odds / 100)
    # A fixed sensitivity haircut, not a statistical confidence interval.
    min_decimal = 1.03 / conservative
    american = -100 / (min_decimal - 1) if min_decimal < 2 else 100 * (min_decimal - 1)
    return dict(conservative_probability=conservative, decimal_odds=decimal,
                estimated_ev=p * decimal - 1, conservative_ev=conservative * decimal - 1,
                minimum_decimal_price=min_decimal, minimum_american_price=american,
                price_pass=decimal >= min_decimal)


def capture(root, date, predictions, picks, now=None):
    from scout_daily import team, name
    from src.sharpie import prepare_sharpie_candidates
    root = Path(root)
    folder = root / "outputs/price_decision_audit"
    folder.mkdir(parents=True, exist_ok=True)
    now = now or dt.datetime.now(dt.timezone.utc)
    schedule = read(root / f"data/processed/schedule_{date}.csv")
    if schedule.empty or predictions.empty:
        reconcile(root)
        return
    candidates = prepare_sharpie_candidates(predictions)
    rows = []
    for _, row in candidates.iterrows():
        games = schedule[
            ((schedule.home_team.map(team) == team(row.team)) & (schedule.away_team.map(team) == team(row.opponent))) |
            ((schedule.away_team.map(team) == team(row.team)) & (schedule.home_team.map(team) == team(row.opponent)))]
        if len(games) != 1:
            continue  # Ambiguous doubleheaders require explicit game identifiers.
        game = games.iloc[0]
        start = pd.to_datetime(game.game_datetime, utc=True, errors="coerce")
        if pd.isna(start) or start <= now or str(game.status).lower() not in {"scheduled", "pre-game", "preview"}:
            continue
        metrics = price_metrics(row.get("sharpie_probability"), row.get("odds"))
        if not metrics:
            continue
        selected = picks[picks.player.map(name).eq(name(row.player)) & picks.team.map(team).eq(team(row.team))] if len(picks) else pd.DataFrame()
        selected = selected.iloc[0] if len(selected) == 1 else pd.Series(dtype=object)
        rows.append(dict(date=date, captured_at_utc=now.isoformat(), start_utc=start.isoformat(),
                         game_pk=game.game_pk, player=row.player, team=team(row.team), opponent=team(row.opponent),
                         version=VERSION, probability=row.sharpie_probability, offered_odds=row.odds,
                         quote_provenance="Model snapshot; sportsbook quote age unverified",
                         decision="On card" if len(selected) else "Not selected",
                         bet_status=selected.get("bet_status", "Not selected"),
                         rank=selected.get("sharpie_rank"), proposed_stake=selected.get("allocation", 0),
                         lineup_confirmed=row.get("confirmed_lineup", False),
                         lineup_slot=row.get("lineup_slot", row.get("batting_order")),
                         actual_bet_odds=None, actual_bet_stake=None, closing_odds=None, **metrics))
    if rows:
        frame = pd.DataFrame(rows)
        token = hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()[:12]
        path = folder / f"snapshot_{date}_{now.strftime('%H%M%S%f')}_{token}.csv"
        with path.open("x", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, index=False)
    reconcile(root)


def reconcile(root):
    from scout_daily import name
    root = Path(root)
    folder = root / "outputs/price_decision_audit"
    frames = [read(p) for p in sorted(folder.glob("snapshot_*.csv"))]
    if not frames:
        return pd.DataFrame()
    data = pd.concat(frames, ignore_index=True)
    data["name_key"] = data.player.map(name)
    # One first-observation row per player/game avoids counting every refresh as a bet.
    data = data.sort_values("captured_at_utc").drop_duplicates(["game_pk", "name_key"])
    results = read(root / "data/processed/pick_results.csv")
    data["actual_hit"] = float("nan")
    data["flat_unit_profit"] = float("nan")
    data["proposed_profit"] = float("nan")
    data["outcome_status"] = "Pending"
    events = read(folder / "price_events.csv")
    if len(events):
        for idx, row in data.iterrows():
            matches = events[number(events.game_pk).eq(number(row.game_pk)) & events.player.map(name).eq(row.name_key)]
            for kind, column in [("actual", "actual_bet_odds"), ("closing", "closing_odds")]:
                event = matches[matches.kind.eq(kind)].sort_values("observed_at_utc")
                if len(event):
                    data.at[idx, column] = event.iloc[-1].odds
                    if kind == "actual":
                        data.at[idx, "actual_bet_stake"] = event.iloc[-1].stake
    if len(results) and "game_pk" in results:
        for idx, row in data.iterrows():
            match = results[number(results.game_pk).eq(number(row.game_pk)) & results.player.map(name).eq(row.name_key)]
            resolved = match.get("resolved", pd.Series(False, index=match.index)).astype(str).str.lower().isin(["true", "1", "1.0"])
            match = match[resolved]
            outcomes = number(match.get("actual_hit", pd.Series(dtype=float))).dropna().unique()
            pa = number(match.get("plate_appearances", pd.Series(dtype=float)))
            if len(outcomes) == 1 and outcomes[0] in (0, 1) and pa.gt(0).any():
                hit = int(outcomes[0])
                profit = row.decimal_odds - 1 if hit else -1
                data.loc[idx, ["actual_hit", "flat_unit_profit", "proposed_profit", "outcome_status"]] = [hit, profit, profit * row.proposed_stake, "Resolved"]
            elif len(match) and pa.notna().all() and pa.eq(0).all():
                data.at[idx, "outcome_status"] = "No PA - excluded (book settlement unverified)"
    target = folder / "first_observation_results.csv"
    temp = target.with_suffix(".tmp")
    data.to_csv(temp, index=False)
    temp.replace(target)
    return data


def record_price(root, game_pk, player, kind, odds, observed_at, source, stake=None):
    """Explicit user-recorded executed/closing quotes; never backfill from model odds."""
    if kind not in {"actual", "closing"} or abs(odds) < 100 or not source.strip():
        raise ValueError("Valid kind, American odds and source are required")
    if kind == "actual" and (stake is None or stake <= 0):
        raise ValueError("Actual wager requires a positive stake")
    stamp = pd.Timestamp(observed_at)
    if stamp.tzinfo is None:
        raise ValueError("Quote timestamp must include timezone")
    folder = Path(root) / "outputs/price_decision_audit"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "price_events.csv"
    event = dict(game_pk=game_pk, player=player, kind=kind, odds=odds, stake=stake,
                 observed_at_utc=stamp.tz_convert("UTC").isoformat(), source=source,
                 recorded_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    pd.DataFrame([event]).to_csv(path, mode="a", header=not path.exists(), index=False)
    reconcile(root)


def render(root):
    import streamlit as st
    st.subheader("Price & Decision Audit")
    st.caption("Prospective shadow audit. First observed pregame decision per player/game; not final locked-card performance or actual betting returns.")
    data = read(Path(root) / "outputs/price_decision_audit/first_observation_results.csv")
    if data.empty:
        st.info("Waiting for eligible pregame snapshots from a model refresh.")
        return
    st.caption("Price pass requires 3% estimated return after subtracting 3 percentage points from the model probability. This is a sensitivity test, not a validated confidence bound. Quote freshness, actual wagers and closing prices are not verified.")
    dates = sorted(data.date.unique(), reverse=True)
    date = st.selectbox("Audit date", dates, key="price_audit_date")
    today = data[data.date.eq(date)]
    st.dataframe(today[["player", "team", "decision", "bet_status", "rank", "probability", "offered_odds", "minimum_american_price", "price_pass", "proposed_stake", "outcome_status"]], hide_index=True, use_container_width=True)
    resolved = data[data.outcome_status.eq("Resolved")].copy()
    if len(resolved):
        resolved["price_test"] = resolved.price_pass.map({True: "Price pass", False: "Price fail"})
        groups = resolved.groupby(["decision", "price_test"]).agg(samples=("actual_hit", "size"), hit_rate=("actual_hit", "mean"), flat_units=("flat_unit_profit", "sum"), flat_roi=("flat_unit_profit", "mean"), proposed_stake=("proposed_stake", "sum"), hypothetical_profit=("proposed_profit", "sum")).reset_index()
        groups["hypothetical_sized_roi"] = groups.hypothetical_profit / groups.proposed_stake.replace(0, float("nan"))
        st.dataframe(groups, hide_index=True, use_container_width=True)
        daily = resolved.groupby(["date", "decision", "price_test"]).flat_unit_profit.sum().unstack(["decision", "price_test"]).fillna(0).cumsum()
        daily.columns = [" / ".join(col) for col in daily.columns]
        st.line_chart(daily)
        st.caption("Each curve assumes one unit on every observation in that group, including unselected players. Groups can have different bet counts; compare ROI and sample size alongside total profit.")
    else:
        st.info("No settled prospective observations yet. Historical wins are not being backfilled into this experiment.")
    st.download_button("Download audit", data.to_csv(index=False), "price_decision_audit.csv", "text/csv")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Record a verified actual-wager or closing price in the audit")
    parser.add_argument("--game-pk", type=int, required=True)
    parser.add_argument("--player", required=True)
    parser.add_argument("--kind", choices=["actual", "closing"], required=True)
    parser.add_argument("--odds", type=float, required=True)
    parser.add_argument("--stake", type=float)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    record_price(Path(__file__).resolve().parent, args.game_pk, args.player, args.kind,
                 args.odds, args.observed_at, args.source, args.stake)
