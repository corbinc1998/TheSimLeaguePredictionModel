import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import config
from src.tracking.logger import load_runs


def diff_predictions(run_a, run_b):
    preds_a = {g["id"]: g for g in run_a["predictions"]}
    preds_b = {g["id"]: g for g in run_b["predictions"]}

    changes = []
    for game_id, pred_b in preds_b.items():
        if game_id not in preds_a:
            continue
        pred_a = preds_a[game_id]

        if pred_a.get("completed") or pred_b.get("completed"):
            continue

        winner_a = pred_a.get("winner")
        winner_b = pred_b.get("winner")
        prob_a = pred_a.get("home_win_prob", 0.5)
        prob_b = pred_b.get("home_win_prob", 0.5)
        shift = abs(prob_a - prob_b)

        if shift < config.DIFF_MIN_SHIFT and winner_a == winner_b:
            continue

        flipped = winner_a != winner_b
        if shift >= config.DIFF_MAJOR_SHIFT:
            severity = "major"
        elif flipped:
            severity = "flip"
        else:
            severity = "minor"

        changes.append({
            "game_id":    game_id,
            "week":       pred_b.get("week"),
            "home_id":    pred_b.get("homeTeamId"),
            "away_id":    pred_b.get("awayTeamId"),
            "winner_was": winner_a,
            "winner_now": winner_b,
            "prob_was":   round(prob_a, 3),
            "prob_now":   round(prob_b, 3),
            "shift":      round(shift, 3),
            "flipped":    flipped,
            "severity":   severity,
        })

    changes.sort(key=lambda x: (0 if x["flipped"] else 1, -x["shift"]))
    return changes


def diff_standings(run_a, run_b):
    standings_a = run_a["standings"]
    standings_b = run_b["standings"]
    changes = []

    for team_id in standings_b:
        if team_id not in standings_a:
            continue
        a = standings_a[team_id]
        b = standings_b[team_id]
        if a["w"] != b["w"] or a["l"] != b["l"]:
            changes.append({
                "team_id":  team_id,
                "abbr":     config.ABBR[team_id],
                "was":      f"{a['w']}-{a['l']}-{a['t']}",
                "now":      f"{b['w']}-{b['l']}-{b['t']}",
                "w_change": b["w"] - a["w"],
                "l_change": b["l"] - a["l"],
            })

    changes.sort(key=lambda x: -abs(x["w_change"]))
    return changes


def diff_bracket(run_a, run_b):
    bracket_a = run_a.get("bracket", {})
    bracket_b = run_b.get("bracket", {})
    changes = []

    for conf in config.CONFERENCES:
        if conf not in bracket_a or conf not in bracket_b:
            continue
        for round_name in ["wildcard", "divisional"]:
            games_a = bracket_a[conf].get(round_name, [])
            games_b = bracket_b[conf].get(round_name, [])
            for i, (ga, gb) in enumerate(zip(games_a, games_b)):
                if ga.get("winner") != gb.get("winner"):
                    changes.append({
                        "conf":       conf,
                        "round":      round_name,
                        "matchup":    f"{config.ABBR[gb['home_id']]} vs {config.ABBR[gb['away_id']]}",
                        "winner_was": config.ABBR.get(ga.get("winner"), "?"),
                        "winner_now": config.ABBR.get(gb.get("winner"), "?"),
                    })

        for round_name in ["conference"]:
            ga = bracket_a[conf].get(round_name, {})
            gb = bracket_b[conf].get(round_name, {})
            if ga.get("winner") != gb.get("winner"):
                changes.append({
                    "conf":       conf,
                    "round":      round_name,
                    "matchup":    f"{config.ABBR.get(gb.get('home_id'), '?')} vs {config.ABBR.get(gb.get('away_id'), '?')}",
                    "winner_was": config.ABBR.get(ga.get("winner"), "?"),
                    "winner_now": config.ABBR.get(gb.get("winner"), "?"),
                })

    sb_a = bracket_a.get("superbowl", {})
    sb_b = bracket_b.get("superbowl", {})
    if sb_a.get("winner") != sb_b.get("winner"):
        changes.append({
            "conf":       "SUPER BOWL",
            "round":      "superbowl",
            "matchup":    f"{config.ABBR.get(sb_b.get('home_id'), '?')} vs {config.ABBR.get(sb_b.get('away_id'), '?')}",
            "winner_was": config.ABBR.get(sb_a.get("winner"), "?"),
            "winner_now": config.ABBR.get(sb_b.get("winner"), "?"),
        })

    return changes


def diff_runs(run_a, run_b):
    return {
        "from_run":    run_a["id"],
        "to_run":      run_b["id"],
        "from_trigger": run_a["trigger"],
        "to_trigger":  run_b["trigger"],
        "predictions": diff_predictions(run_a, run_b),
        "standings":   diff_standings(run_a, run_b),
        "bracket":     diff_bracket(run_a, run_b),
    }


if __name__ == "__main__":
    runs = load_runs()
    if len(runs) < 2:
        print("Need at least 2 runs to diff — run logger.py again to generate a second run")
    else:
        diff = diff_runs(runs[-2], runs[-1])
        print(f"\nDiff: {diff['from_trigger']} → {diff['to_trigger']}")

        print(f"\nPrediction changes: {len(diff['predictions'])}")
        for c in diff["predictions"]:
            flip = "FLIP" if c["flipped"] else "SHIFT"
            print(f"  [{flip}] W{c['week']} {config.ABBR.get(c['home_id'], '?')} vs {config.ABBR.get(c['away_id'], '?')} — {config.ABBR.get(c['winner_was'], '?')} → {config.ABBR.get(c['winner_now'], '?')} ({c['prob_was']} → {c['prob_now']})")

        print(f"\nStandings changes: {len(diff['standings'])}")
        for c in diff["standings"]:
            print(f"  {c['abbr']}: {c['was']} → {c['now']}")

        print(f"\nBracket changes: {len(diff['bracket'])}")
        for c in diff["bracket"]:
            print(f"  [{c['conf']} {c['round'].upper()}] {c['matchup']}: {c['winner_was']} → {c['winner_now']}")