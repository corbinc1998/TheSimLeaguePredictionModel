import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games

def get_home_away_splits(team_id, games):
    home = {"w" : 0, "l" : 0, "t" : 0, "point_diff" : 0, "games": 0 }
    away = {"w" : 0, "l" : 0, "t" : 0, "point_diff" : 0, "games": 0 }
    # homeTeamId homeScore
    # awayTeamId awayScore
    for game in games:
        if not game.get("completed", False):
            continue
        # Home
        if game["homeTeamId"] == team_id:
            home["games"] += 1
            home["point_diff"] += game["homeScore"] - game["awayScore"]
            if game["homeScore"] > game["awayScore"]:
                home["w"] += 1
            elif game["homeScore"]< game["awayScore"]:
                home["l"] += 1
            else:
                home["t"] += 1
        # Away
        if game["awayTeamId"] == team_id:
            away["games"] += 1
            away["point_diff"] += game["awayScore"] - game["homeScore"]
            if game["awayScore"] > game["homeScore"]:
                away["w"] += 1
            elif game["awayScore"]< game["homeScore"]:
                away["l"] += 1
            else:
                away["t"] += 1
    return {"home": home, "away": away}

def get_home_boost(team_id, games):
    splits = get_home_away_splits(team_id, games)
    home_avg = splits["home"]["point_diff"] / splits["home"]["games"] if splits["home"]["games"] > 0 else 0
    away_avg = splits["away"]["point_diff"] / splits["away"]["games"] if splits["away"]["games"] > 0 else 0
    home_boost = home_avg - away_avg
    return home_boost

# Testing
# games = load_games()
# print(get_home_boost("bal", games))
# print(get_home_boost("pit", games))
# print(get_home_away_splits("bal", games))
# print(get_home_away_splits("pit", games))
    

