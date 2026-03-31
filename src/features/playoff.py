import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games
import config
def get_playoff_record(team_id, games):
    playoff_games = {"w": 0, "l": 0, "points": 0, "games": 0}
    for game in games:
        if not game.get("completed", False):
            continue
        if game.get("isPlayoff") and (game["homeTeamId"] == team_id or game["awayTeamId"] == team_id):
            playoff_games["games"] += 1
            if game["homeTeamId"] == team_id and game["homeScore"] > game["awayScore"]:
                playoff_games["w"] += 1
                playoff_games["points"] += game["homeScore"]
            elif game["awayTeamId"] == team_id and game["awayScore"] > game["homeScore"]:
                playoff_games["w"] += 1
                playoff_games["points"] += game["awayScore"]
            else:
                playoff_games["l"] += 1
                if game["homeTeamId"] == team_id:
                    playoff_games["points"] += game["homeScore"]
                else:
                    playoff_games["points"] += game["awayScore"]
    if playoff_games["games"] < config.MIN_SAMPLE_PLAYOFF:
        return None
    playoff_games["ppg"] = playoff_games["points"] / playoff_games["games"]
    return playoff_games
    

# Testing
# games = load_games()
# print(get_playoff_record("chi", games))
# print(get_playoff_record("was", games))

def get_playoff_clutch(team_id, games):
    points = 0
    regular_season_games = 0
    playoff_record = get_playoff_record(team_id, games)
    if playoff_record is None:
        return 0.0
    for game in games:
        if not game.get("completed", False):
            continue
        if game.get("isPlayoff"):
            continue
        if game["homeTeamId"] == team_id:
            points += game["homeScore"]
            regular_season_games += 1
        elif game["awayTeamId"] == team_id:
            points += game["awayScore"]
            regular_season_games += 1
    if regular_season_games == 0:
        return 0.0
    regular_season_ppg = points / regular_season_games
    return playoff_record["ppg"] - regular_season_ppg

# Testing
# games = load_games()
# print(get_playoff_clutch("chi", games))
# print(get_playoff_clutch("no", games))
# print(get_playoff_clutch("was", games))