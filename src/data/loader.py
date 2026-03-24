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
        # Just see the top level keys
        # print(d.keys())

        # See the season names
        # print(d["seasons"].keys())

        # See just the first game of season 1
        # print(d["seasons"]["1"]["games"][0])    

    games = []
    for season_name, season in d["seasons"].items():
        season_number = get_season_number(season_name)
        for game in season["games"]:
            game["season"] = season_number
            games.append(game)

            # games = load_games()
            # print(len(games))
            # print(games[0])

    return games






def load_team_stats(team_id):
    team_name = config.TEAM_STAT_FILES[team_id]
    with open(os.path.join(config.TEAM_STATS_DIR, f"{team_name}.json")) as f:
        d = json.load(f)
        
    return d