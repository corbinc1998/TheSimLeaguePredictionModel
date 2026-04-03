import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from datetime import datetime
import config


def create_run(trigger, season_id, current_week, predictions, standings, seeds, bracket):
    return {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now().isoformat(),
        "trigger": trigger,
        "season_id": season_id,
        "current_week": current_week,
        "predictions": predictions,
        "standings": standings,
        "seeds": seeds,
        "bracket": bracket,
    }


def save_run(run):
    runs = load_runs()
    runs.append(run)
    os.makedirs(os.path.dirname(config.PREDICTIONS_PATH), exist_ok=True)
    with open(config.PREDICTIONS_PATH, "w") as f:
        json.dump(runs, f, indent=2)


def load_runs():
    if not os.path.exists(config.PREDICTIONS_PATH):
        return []
    with open(config.PREDICTIONS_PATH) as f:
        return json.load(f)


def get_latest_run():
    runs = load_runs()
    if not runs:
        return None
    return sorted(runs, key=lambda x: x["timestamp"])[-1]


if __name__ == "__main__":
    from src.data.loader import load_games, load_team_stats
    from src.features.elo import compute_elo_ratings
    from src.simulation.season import predict_season
    from src.simulation.standings import build_standings, build_division_standings, get_playoff_seeds
    from src.simulation.bracket import simulate_bracket

    games = load_games()
    elo_ratings, elo_history = compute_elo_ratings(games)

    team_stats_map = {}
    for tid in config.TEAM_IDS:
        try:
            team_stats_map[tid] = load_team_stats(tid)
        except:
            team_stats_map[tid] = None

    results = predict_season(games, team_stats_map, season_id=8, current_week=1, elo_ratings=elo_ratings)
    standings = build_standings(results)
    seeds = get_playoff_seeds(standings, games)
    bracket = simulate_bracket(seeds, games, team_stats_map, season_id=8, elo_ratings=elo_ratings)

    run = create_run(
        trigger="Initial S8 prediction",
        season_id=8,
        current_week=1,
        predictions=results,
        standings=standings,
        seeds=seeds,
        bracket=bracket
    )

    save_run(run)
    print(f"Run saved: {run['id']}")
    print(f"Total runs logged: {len(load_runs())}")

    latest = get_latest_run()
    print(f"Latest run trigger: {latest['trigger']}")