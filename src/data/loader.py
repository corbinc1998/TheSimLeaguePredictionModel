import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import re
import json
import config


def get_season_number(name):
    match = re.search(r'\d+', str(name))
    return int(match.group()) if match else None


def load_games():
    with open(config.GAMES_PATH) as f:
        d = json.load(f)

    games = []
    for season_name, season in d["seasons"].items():
        season_number = get_season_number(season_name)
        for game in season["games"]:
            game["season"] = season_number
            if "completed" not in game:
                game["completed"] = game.get("status") == "final"
            games.append(game)

    return games


def load_team_stats(team_id):
    team_name = config.TEAM_STAT_FILES[team_id]
    with open(os.path.join(config.TEAM_STATS_DIR, f"{team_name}.json")) as f:
        d = json.load(f)

    return d


def load_team_stats_map():
    """
    Load every team's stats report into {team_id: report}.
    A missing file maps to None and is reported, instead of being
    silently swallowed by a bare except.
    """
    team_stats_map = {}
    for team_id in config.TEAM_IDS:
        try:
            team_stats_map[team_id] = load_team_stats(team_id)
        except FileNotFoundError:
            print(f"  [warn] no team stats file for {team_id} "
                  f"({config.TEAM_STAT_FILES[team_id]}.json)")
            team_stats_map[team_id] = None
    return team_stats_map


def as_of(games, season_id, week):
    """
    Return a copy of games as they looked right before (season_id, week).

    Every completed game at or after that point is marked unplayed with
    its scores removed. All feature code already skips games that are
    not completed, so passing this list in guarantees nothing downstream
    can see a result from the future. Used by the backtest.
    """
    cutoff = (season_id, week)
    masked = []
    for game in games:
        if game.get("completed") and (game["season"], game["week"]) >= cutoff:
            game = {**game, "completed": False, "homeScore": None, "awayScore": None}
        masked.append(game)
    return masked