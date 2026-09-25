"""
Walk-forward backtest.

Replays a season one week at a time. Before each week, every result from
that week onward is hidden (loader.as_of), Elo is recomputed from what was
known then, and that week's games are predicted. Nothing a prediction uses
can come from its own game or any later one.

Usage (from the repo root):
    python -m src.evaluation.backtest --fit
        Replay config.TRAIN_SEASONS and print fitted values for
        LOGISTIC_SCALE, HOME_FIELD_ADVANTAGE and POINTS_PER_EDGE.

    python -m src.evaluation.backtest --seasons 8 9
        Replay the given seasons with the current config, score them, and
        compare against the predictions originally logged in
        predictions_log.json. Writes results to data/processed/backtests/.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import argparse
import json
import math
from datetime import datetime

import config
from src.data.loader import load_games, load_team_stats_map, as_of
from src.features.elo import compute_elo_ratings, is_neutral_site
from src.features.ratings import build_matchup_features
from src.model.predict import predict_game, compute_edge


# ── Replay ────────────────────────────────────────────────────────────────────

def home_result(game):
    if game["homeScore"] > game["awayScore"]:
        return 1.0
    if game["homeScore"] < game["awayScore"]:
        return 0.0
    return 0.5


def replay_season(games, team_stats_map, season_id):
    """Predict every completed game of season_id using only prior information."""
    season_games = [g for g in games if g["season"] == season_id and g.get("completed")]
    weeks = sorted({g["week"] for g in season_games})
    rows = []

    for week in weeks:
        known = as_of(games, season_id, week)
        elo_ratings, _ = compute_elo_ratings(known, as_of_season=season_id)

        for game in (g for g in season_games if g["week"] == week):
            features = build_matchup_features(
                game["homeTeamId"], game["awayTeamId"],
                known, team_stats_map,
                as_of_week=week,
                season_id=season_id,
                elo_ratings=elo_ratings,
                is_playoff=bool(game.get("isPlayoff")),
                is_neutral=is_neutral_site(game),
            )
            prediction = predict_game(features)
            result = home_result(game)
            rows.append({
                "game_id":       game["id"],
                "season":        season_id,
                "week":          week,
                "is_playoff":    bool(game.get("isPlayoff")),
                "home_id":       game["homeTeamId"],
                "away_id":       game["awayTeamId"],
                "features":      features,
                "home_win_prob": round(prediction["home_win_prob"], 4),
                "winner":        prediction["winner"],
                "home_result":   result,
                "margin":        game["homeScore"] - game["awayScore"],
            })
        print(f"  S{season_id} W{week:<2} done", end="\r")
    print(" " * 30, end="\r")
    return rows


# ── Scoring ───────────────────────────────────────────────────────────────────

def score(pairs):
    """
    pairs: list of (home_win_prob, home_result). Ties are excluded.
    Returns accuracy, Brier score and log loss. Lower Brier/log loss is
    better; always predicting 50% scores 0.25 Brier and 0.693 log loss.
    """
    pairs = [(p, r) for p, r in pairs if r != 0.5]
    if not pairs:
        return None
    n = len(pairs)
    correct = sum(1 for p, r in pairs if (p >= 0.5) == (r == 1.0))
    brier = sum((p - r) ** 2 for p, r in pairs) / n
    eps = 1e-9
    log_loss = -sum(math.log(max(eps, p if r == 1.0 else 1 - p)) for p, r in pairs) / n
    return {
        "games": n,
        "correct": correct,
        "accuracy": round(correct / n, 3),
        "brier": round(brier, 4),
        "log_loss": round(log_loss, 4),
    }


def calibration_table(pairs, bins=10):
    """Group predictions by favorite's probability and compare to how often the favorite won."""
    table = {}
    for p, r in pairs:
        if r == 0.5:
            continue
        fav_prob = max(p, 1 - p)
        fav_won = (p >= 0.5) == (r == 1.0)
        b = min(int(fav_prob * bins), bins - 1)
        entry = table.setdefault(b, {"n": 0, "wins": 0, "prob_sum": 0.0})
        entry["n"] += 1
        entry["wins"] += fav_won
        entry["prob_sum"] += fav_prob
    return [
        {
            "bucket": f"{b * 100 // bins}-{(b + 1) * 100 // bins}%",
            "games": e["n"],
            "avg_predicted": round(e["prob_sum"] / e["n"], 3),
            "favorite_won": round(e["wins"] / e["n"], 3),
        }
        for b, e in sorted(table.items())
    ]


# ── Original predictions (baseline) ───────────────────────────────────────────

def load_logged_predictions(games):
    """
    For each game, the last prediction logged before its result was entered.
    Regular season comes from each run's predictions; playoffs come from each
    run's bracket (entries without "actual").
    Returns {game_id: home_win_prob}.
    """
    if not os.path.exists(config.PREDICTIONS_PATH):
        return {}
    with open(config.PREDICTIONS_PATH) as f:
        runs = json.load(f)
    runs.sort(key=lambda r: r["timestamp"])

    playoff_lookup = {}
    for g in games:
        if g.get("isPlayoff") and g.get("completed"):
            playoff_lookup[(g["season"], frozenset((g["homeTeamId"], g["awayTeamId"])))] = g

    logged = {}
    for run in runs:
        for p in run.get("predictions", []):
            if p.get("predicted") and p.get("home_win_prob") is not None:
                logged[p["id"]] = p["home_win_prob"]

        bracket = run.get("bracket") or {}
        entries = []
        for conf in config.CONFERENCES:
            if conf in bracket:
                entries += bracket[conf].get("wildcard", [])
                entries += bracket[conf].get("divisional", [])
                entries.append(bracket[conf].get("conference"))
        entries.append(bracket.get("superbowl"))
        for e in entries:
            if not e or e.get("actual") or e.get("home_win_prob") is None:
                continue
            g = playoff_lookup.get((run["season_id"], frozenset((e["home_id"], e["away_id"]))))
            if g is None:
                continue
            prob = e["home_win_prob"] if e["home_id"] == g["homeTeamId"] else 1 - e["home_win_prob"]
            logged[g["id"]] = prob
    return logged


# ── Fitting ───────────────────────────────────────────────────────────────────

def fit(rows):
    """
    Grid-search LOGISTIC_SCALE and HOME_FIELD_ADVANTAGE by log loss, and fit
    POINTS_PER_EDGE by least squares (margin = POINTS_PER_EDGE * edge).
    Only the rows passed in are used, so pass training seasons only.
    """
    saved_hfa = config.HOME_FIELD_ADVANTAGE
    config.HOME_FIELD_ADVANTAGE = 0.0
    data = []
    for row in rows:
        if row["home_result"] == 0.5:
            continue
        edge0 = compute_edge(row["features"])
        home_site = 0.0 if row["features"].get("is_neutral") else 1.0
        data.append((edge0, home_site, row["home_result"], row["margin"]))
    config.HOME_FIELD_ADVANTAGE = saved_hfa

    def log_loss(scale, hfa):
        total = 0.0
        for edge0, home_site, result, _ in data:
            p = 1 / (1 + math.exp(-(edge0 + hfa * home_site) * scale))
            p = min(max(p, 1e-9), 1 - 1e-9)
            total -= math.log(p if result == 1.0 else 1 - p)
        return total / len(data)

    best = None
    for scale_step in range(0, 101):
        scale = scale_step * 0.002
        for hfa_step in range(-10, 11):
            hfa = hfa_step * 0.5
            ll = log_loss(scale, hfa)
            if best is None or ll < best[0]:
                best = (ll, scale, hfa)

    _, scale, hfa = best
    edges = [e + hfa * s for e, s, _, _ in data]
    margins = [m for _, _, _, m in data]
    denom = sum(e * e for e in edges)
    points_per_edge = sum(e * m for e, m in zip(edges, margins)) / denom if denom else 0.0

    return {
        "LOGISTIC_SCALE": round(scale, 4),
        "HOME_FIELD_ADVANTAGE": round(hfa, 2),
        "POINTS_PER_EDGE": round(points_per_edge, 3),
        "train_log_loss": round(best[0], 4),
        "coin_flip_log_loss": round(math.log(2), 4),
        "train_games": len(data),
    }


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_scores(label, s):
    if s is None:
        print(f"  {label:<24} no games")
        return
    print(f"  {label:<24} {s['correct']:>3}/{s['games']:<3} ({s['accuracy']*100:.1f}%)   "
          f"Brier {s['brier']:.4f}   log loss {s['log_loss']:.4f}")


def run_backtest(seasons):
    games = load_games()
    team_stats_map = load_team_stats_map()
    logged = load_logged_predictions(games)

    report = {"created": datetime.now().isoformat(), "config": {
        "LOGISTIC_SCALE": config.LOGISTIC_SCALE,
        "HOME_FIELD_ADVANTAGE": config.HOME_FIELD_ADVANTAGE,
        "POINTS_PER_EDGE": config.POINTS_PER_EDGE,
        "ELO_SEASON_REGRESSION": config.ELO_SEASON_REGRESSION,
        "ELO_HOME_ADVANTAGE": config.ELO_HOME_ADVANTAGE,
        "ELO_RATING_WEIGHT": config.ELO_RATING_WEIGHT,
        "PRIOR_BLEND_K": config.PRIOR_BLEND_K,
        "WEIGHTS": config.WEIGHTS,
    }, "seasons": {}}

    all_new, all_old = [], []
    for season_id in seasons:
        print(f"\nReplaying Season {season_id}...")
        rows = replay_season(games, team_stats_map, season_id)

        new_pairs = [(r["home_win_prob"], r["home_result"]) for r in rows]
        old_pairs = [(logged[r["game_id"]], r["home_result"]) for r in rows if r["game_id"] in logged]
        # Compare on exactly the same games
        same_ids = {r["game_id"] for r in rows if r["game_id"] in logged}
        new_same = [(r["home_win_prob"], r["home_result"]) for r in rows if r["game_id"] in same_ids]

        reg = [r for r in rows if not r["is_playoff"]]
        post = [r for r in rows if r["is_playoff"]]

        season_report = {
            "new_all": score(new_pairs),
            "new_regular": score([(r["home_win_prob"], r["home_result"]) for r in reg]),
            "new_playoffs": score([(r["home_win_prob"], r["home_result"]) for r in post]),
            "new_on_logged_games": score(new_same),
            "old_on_logged_games": score(old_pairs),
            "calibration_new": calibration_table(new_pairs),
            "calibration_old": calibration_table(old_pairs),
            "games": [{k: v for k, v in r.items() if k != "features"} | {
                "old_home_win_prob": logged.get(r["game_id"])} for r in rows],
        }
        report["seasons"][str(season_id)] = season_report
        all_new += new_same
        all_old += old_pairs

        print(f"Season {season_id}  (same {len(same_ids)} games for both models)")
        print_scores("original model", season_report["old_on_logged_games"])
        print_scores("updated model", season_report["new_on_logged_games"])
        print_scores("  updated, reg season", season_report["new_regular"])
        print_scores("  updated, playoffs", season_report["new_playoffs"])

    print("\nCombined")
    print_scores("original model", score(all_old))
    print_scores("updated model", score(all_new))
    report["combined"] = {"old": score(all_old), "new": score(all_new),
                          "calibration_old": calibration_table(all_old),
                          "calibration_new": calibration_table(all_new)}

    print("\nCalibration (favorite's predicted chance vs how often it won)")
    print(f"  {'bucket':<10}{'original':>24}{'updated':>24}")
    old_cal = {c["bucket"]: c for c in report["combined"]["calibration_old"]}
    new_cal = {c["bucket"]: c for c in report["combined"]["calibration_new"]}
    for bucket in sorted(set(old_cal) | set(new_cal)):
        def cell(c):
            return f"{c['games']:>3} g, won {c['favorite_won']*100:>3.0f}%" if c else "-"
        print(f"  {bucket:<10}{cell(old_cal.get(bucket)):>24}{cell(new_cal.get(bucket)):>24}")

    os.makedirs(config.BACKTEST_DIR, exist_ok=True)
    name = f"backtest_S{'_S'.join(str(s) for s in seasons)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    path = os.path.join(config.BACKTEST_DIR, name)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {path}")
    return report


def run_fit():
    games = load_games()
    team_stats_map = load_team_stats_map()
    rows = []
    for season_id in config.TRAIN_SEASONS:
        print(f"Replaying training Season {season_id}...")
        rows += replay_season(games, team_stats_map, season_id)
    result = fit(rows)
    print("\nFitted on seasons", config.TRAIN_SEASONS)
    for k, v in result.items():
        print(f"  {k}: {v}")
    print("\nCopy LOGISTIC_SCALE, HOME_FIELD_ADVANTAGE and POINTS_PER_EDGE into config.py.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walk-forward backtest")
    parser.add_argument("--fit", action="store_true", help="fit calibration values on TRAIN_SEASONS")
    parser.add_argument("--seasons", type=int, nargs="+", default=[8, 9])
    args = parser.parse_args()

    if args.fit:
        run_fit()
    else:
        overlap = set(args.seasons) & set(config.TRAIN_SEASONS)
        if overlap:
            print(f"[warn] seasons {sorted(overlap)} are in TRAIN_SEASONS; their scores are not out-of-sample")
        run_backtest(args.seasons)