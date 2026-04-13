import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

import argparse
from src.data.loader import load_games, load_team_stats
from src.features.elo import compute_elo_ratings
from src.simulation.season import predict_season
from src.simulation.standings import build_standings, get_playoff_seeds
from src.simulation.bracket import simulate_bracket
from src.tracking.logger import create_run, save_run, get_latest_run
from src.tracking.diff import diff_runs
import config


def run(trigger, season_id, current_week):
    print(f"\n{'='*50}")
    print(f"MADDEN PREDICT — Season {season_id} Week {current_week}")
    print(f"Trigger: {trigger}")
    print(f"{'='*50}\n")

    # Step 1 — Load data
    print("Loading games and team stats...")
    games = load_games()
    team_stats_map = {}
    for tid in config.TEAM_IDS:
        try:
            team_stats_map[tid] = load_team_stats(tid)
        except:
            team_stats_map[tid] = None
    loaded = sum(1 for v in team_stats_map.values() if v is not None)
    print(f"  {len(games)} games loaded across all seasons")
    print(f"  {loaded}/32 team stat files loaded")

    # Step 2 — Compute Elo
    print("\nComputing Elo ratings...")
    elo_ratings, elo_history = compute_elo_ratings(games)
    top3 = sorted(elo_ratings.items(), key=lambda x: -x[1])[:3]
    print(f"  Top 3: {', '.join(f'{config.ABBR[t]} ({round(r,1)})' for t,r in top3)}")

    # Step 3 — Predict season
    print(f"\nPredicting Season {season_id}...")
    results = predict_season(games, team_stats_map, season_id=season_id, current_week=current_week, elo_ratings=elo_ratings)
    completed = sum(1 for g in results if g.get("completed"))
    predicted = sum(1 for g in results if g.get("predicted"))
    print(f"  {completed} completed games, {predicted} predicted games")

    # Step 4 — Build standings
    print("\nBuilding standings...")
    standings = build_standings(results)
    seeds = get_playoff_seeds(standings, games)

    # Step 5 — Simulate bracket
    print("Simulating playoff bracket...")
    bracket = simulate_bracket(seeds, games, team_stats_map, season_id=season_id, elo_ratings=elo_ratings)
    if "champion" in bracket:
        print(f"  Projected Super Bowl champion: {config.ABBR[bracket['champion']]}")

    # Step 6 — Diff against previous run
    previous_run = get_latest_run()
    new_run = create_run(
        trigger=trigger,
        season_id=season_id,
        current_week=current_week,
        predictions=results,
        standings=standings,
        seeds=seeds,
        bracket=bracket
    )

    if previous_run:
        print("\nDiffing against previous run...")
        diff = diff_runs(previous_run, new_run)
        pred_changes = diff["predictions"]
        stand_changes = diff["standings"]
        bracket_changes = diff["bracket"]

        flips = [c for c in pred_changes if c["flipped"]]
        majors = [c for c in pred_changes if c["severity"] == "major" and not c["flipped"]]
        minors = [c for c in pred_changes if c["severity"] == "minor"]

        print(f"\n  Prediction changes:")
        print(f"    Flips:        {len(flips)}")
        print(f"    Major shifts: {len(majors)}")
        print(f"    Minor shifts: {len(minors)}")

        if flips:
            print("\n  FLIPPED PREDICTIONS:")
            for c in flips:
                h = config.ABBR.get(c["home_id"], "?")
                a = config.ABBR.get(c["away_id"], "?")
                was = config.ABBR.get(c["winner_was"], "?")
                now = config.ABBR.get(c["winner_now"], "?")
                print(f"    W{c['week']} {h} vs {a}: {was} → {now} ({round(c['prob_was']*100)}% → {round(c['prob_now']*100)}%)")

        if stand_changes:
            print(f"\n  STANDINGS CHANGES: {len(stand_changes)} teams")
            for c in stand_changes[:5]:
                print(f"    {c['abbr']}: {c['was']} → {c['now']}")

        if bracket_changes:
            print(f"\n  BRACKET CHANGES:")
            for c in bracket_changes:
                print(f"    [{c['conf']} {c['round'].upper()}] {c['winner_was']} → {c['winner_now']}")
    else:
        print("\nNo previous run found — this is the baseline prediction")

    # Step 7 — Save run
    save_run(new_run)
    print(f"\nRun saved: {new_run['id']}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Madden Predict Pipeline")
    parser.add_argument("--season",  type=int, default=config.CURRENT_SEASON)
    parser.add_argument("--week",    type=int, default=1)
    parser.add_argument("--trigger", type=str, default="Manual run")
    args = parser.parse_args()

    run(
        trigger=args.trigger,
        season_id=args.season,
        current_week=args.week
    )