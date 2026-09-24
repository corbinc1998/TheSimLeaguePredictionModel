import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from datetime import datetime
import config


def create_run(trigger, season_id, current_week, predictions, standings, seeds, bracket, elo_ratings=None, team_ratings=None, power_rankings=None, projections=None):
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
        "elo_ratings": elo_ratings or {},
        "team_ratings": team_ratings or {},
        "power_rankings": power_rankings or [],
        "projections": projections or {},
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
    # Runs are created by pipeline.py. This just summarizes the log.
    runs = load_runs()
    print(f"Total runs logged: {len(runs)}")
    latest = get_latest_run()
    if latest:
        print(f"Latest run: S{latest['season_id']} W{latest['current_week']} - {latest['trigger']}")