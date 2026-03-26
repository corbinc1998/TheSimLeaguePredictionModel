import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games
import config
# Returns all completed games between two specific teams across all seasons
def get_h2h_games(team_a, team_b, games):
    h2h_games = []
    for game in games:
        if not game["completed"]:
            continue
        if (game["homeTeamId"] == team_a and game["awayTeamId"] == team_b) or (game["homeTeamId"] == team_b and game["awayTeamId"] == team_a):
            h2h_games.append(game)
    return h2h_games

# Testing
# games = load_games()
# number of games: print(len(get_h2h_games("chi", "bal", games)))
# print(get_h2h_games("chi", "bal", games))


# current_season should be the most recently COMPLETED season, not the upcoming one
# This ensures decay weights are calculated correctly relative to finished seasons
# e.g. pass 7 when S7 is the last completed season, even if S8 is current
def get_h2h_record(team_a, team_b, games, current_season):
    team_a_record = {"w" : 0, "l" : 0, "t" : 0, "games": 0 }
    h2h_games = get_h2h_games(team_a,team_b, games)
    # If there aren't enough matchups between these two teams, we can't trust
    # the h2h history as a meaningful signal — return 0.5 (no edge either way)
    if len(h2h_games) < config.MIN_SAMPLE_H2H:
        return 0.5
    # weighted_wins = 0
    total_weight = 0      
    team_a_record["games"] = len(h2h_games)
    for game in h2h_games:
        weight = config.H2H_DECAY ** (current_season - game["season"])
        if game.get("isPlayoff"):
            weight *= 1.5
        if (game["homeTeamId"] == team_a and game["homeScore"] > game["awayScore"]) or (game["awayTeamId"] == team_a and game["awayScore"] > game["homeScore"]):
            team_a_record["w"] += weight
            total_weight += weight
        elif (game["homeTeamId"] == team_a and game["homeScore"] < game["awayScore"]) or (game["awayTeamId"] == team_a and game["awayScore"] < game["homeScore"]):
            team_a_record["l"] += weight
            total_weight += weight
        else:  
            team_a_record["t"] += weight
            total_weight += weight
    return team_a_record["w"] / total_weight

# Testing 
# games = load_games()
# print(get_h2h_record('bal','pit',games,7))    

def get_h2h_margin(team_a, team_b, games, current_season):
    h2h_games = get_h2h_games(team_a,team_b, games)
    if len(h2h_games) < config.MIN_SAMPLE_H2H:
        return 0.0
    team_a_margin = 0
    total_weight = 0 
    for game in h2h_games:
        weight = config.H2H_DECAY ** (current_season - game["season"])
        if game.get("isPlayoff"):
            weight *= 1.5
        if game["homeTeamId"]  == team_a:
            team_a_margin += (game["homeScore"] - game["awayScore"]) * weight
            total_weight += weight
        elif game["awayTeamId"]  == team_a:
            team_a_margin += (game["awayScore"] - game["homeScore"]) * weight
            total_weight += weight
    return team_a_margin / total_weight
            
# Testing
# games = load_games()
# print(get_h2h_margin("bal", "pit", games, 7))