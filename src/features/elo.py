import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games
import config

def compute_elo_ratings(games):
    elo_ratings = {team_id: config.ELO_INITIAL for team_id in config.TEAM_IDS}
    elo_history = [] 
    games = sorted(games, key=lambda x: (x["season"], x["week"]))
    for game in games:
        if not game["completed"]:
            continue
        if game.get("isPlayoff"):
            k = config.ELO_K_PLAYOFF
        else:
            k = config.ELO_K_FACTOR
        home_team = game["homeTeamId"]
        away_team = game["awayTeamId"]
        expected_home = 1 / (1 + 10 ** ((elo_ratings[away_team] - elo_ratings[home_team]) / 400))
        expected_away = 1 - expected_home
       
        if game["homeScore"] > game["awayScore"]:
            home_actual, away_actual = 1, 0
        elif game["awayScore"] > game["homeScore"]:
            home_actual, away_actual = 0, 1
        else:
            home_actual, away_actual = 0.5, 0.5

        elo_ratings[home_team] += k * (home_actual - expected_home)
        elo_ratings[away_team] += k * (away_actual - expected_away)

        elo_history.append({
            "season": game["season"],
            "week": game["week"],
            "game_id": game["id"],
            "ratings": dict(elo_ratings)  # copy of current ratings
            })
            
           
    
    return elo_ratings, elo_history
                 

# Testing
# if __name__ == "__main__":
#     games = load_games()
#     ratings, history = compute_elo_ratings(games)
#     for team_id, rating in sorted(ratings.items(), key=lambda x: -x[1]):
#         print(f"{team_id}: {round(rating, 1)}")
#     print(f"\nTotal snapshots: {len(history)}")
#     print("First snapshot:", history[0])
#     print("Last snapshot:", history[-1])


def get_win_probability(team_a_elo, team_b_elo, is_home):
    elo_gap = team_a_elo - team_b_elo
    if is_home:
        elo_gap += config.ELO_HOME_ADVANTAGE
    else:
        elo_gap -= config.ELO_HOME_ADVANTAGE
    expected = 1 / (1 + 10 ** (-elo_gap / 400))
    return expected



def get_best_wins(team_id, games, elo_history):
    history_by_game = {}
    for snapshot in elo_history:
        history_by_game[snapshot["game_id"]] = snapshot
    wins = []
    for game in games:
        if not game["completed"]:
            continue
        if game['homeTeamId'] == team_id and game['homeScore'] > game['awayScore']:
            snapshot = history_by_game[game["id"]]
            opponent_id = game['awayTeamId']
            opponent_elo = snapshot["ratings"][opponent_id]
            wins.append({
            "opponent_id": opponent_id,
            "opponent_elo": opponent_elo,
            "season": game["season"],
            "week": game["week"],
            "score": f"{game['homeScore']}-{game['awayScore']}"
            })
        elif game['awayTeamId'] == team_id and game['awayScore'] > game['homeScore']:
            snapshot = history_by_game[game["id"]]
            opponent_id = game['homeTeamId']
            opponent_elo = snapshot["ratings"][opponent_id]
            wins.append({
                "opponent_id": opponent_id,
                "opponent_elo": opponent_elo,
                "season": game["season"],
                "week": game["week"],
                "score": f"{game['awayScore']}-{game['homeScore']}"
            })
    
    wins.sort(key=lambda x: -x["opponent_elo"])
    return wins[:10]
 


# Testing
# if __name__ == "__main__":
#     games = load_games()
#     ratings, history = compute_elo_ratings(games)
#     for team_id, rating in sorted(ratings.items(), key=lambda x: -x[1]):
#         print(f"{team_id}: {round(rating, 1)}")
#     print(f"\nTotal snapshots: {len(history)}")
#     print("First snapshot:", history[0])
#     print("Last snapshot:", history[-1])

#     print("\n--- get_win_probability ---")
#     chi_elo = ratings["chi"]
#     bal_elo = ratings["bal"]
#     print(f"Bears vs Ravens (Bears at home): {round(get_win_probability(chi_elo, bal_elo, True), 3)}")
#     print(f"Bears vs Ravens (Ravens at home): {round(get_win_probability(chi_elo, bal_elo, False), 3)}")
#     print("\n--- get_best_wins ---")
# best_wins = get_best_wins("chi", games, history)
# for win in best_wins:
#     print(f"S{win['season']} W{win['week']} vs {win['opponent_id'].upper()} ({round(win['opponent_elo'], 1)}) — {win['score']}")
