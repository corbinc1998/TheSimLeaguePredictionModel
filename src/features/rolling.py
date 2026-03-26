import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games
import config
#  rolling.py
# NOTE: Currently limited to game result data (win%, PPG, points allowed, point diff, streak)
# Week-by-week box score stats (yards, turnovers, red zone %, third down %) will be added
# once per-game stat tracking is implemented in the data pipeline
# At that point rolling will also include: rolling_yards_pg, rolling_turnover_diff,
# rolling_redzone_pct, rolling_third_down_pct


# rolling.py
# This module answers: how has a team been performing recently?
#
# FUNCTION 1 — get_rolling_stats(team_id, games, as_of_week, season_id, window=None)
# Returns a team's stats over their last N games as of a specific week
# CRITICAL: only include games BEFORE as_of_week in season_id — never include
# the game being predicted or any future games (this is data leakage)
# If window is None use config.ROLLING_WINDOW
# If team has fewer than config.MIN_GAMES_PLAYED return None — not enough data

def get_rolling_stats(team_id, games, as_of_week, season_id, window=None):
    cutoff = as_of_week - 1
    if window is None:
            window = config.ROLLING_WINDOW
    filtered = []
    for game in games:
        if not game["completed"]:
            continue
        if game["season"] == season_id and game["week"] <= cutoff:
            if game["homeTeamId"] == team_id or game["awayTeamId"] == team_id:
                filtered.append(game)
    # Sort by week ascending so [-window:] grabs the most recent games
    # lambda x: x['week'] == "for each item x in the list, use its week value to sort"
    filtered.sort(key=lambda x: x['week'])
    filtered = filtered[-window:]  # take the most recent N games
    if len(filtered) < config.MIN_GAMES_PLAYED:
        return None
    wins = 0
    losses = 0
    home_wins = 0
    away_wins = 0
    home_losses = 0
    away_losses = 0
    ties = 0
    home_ties = 0
    away_ties = 0
    points_scored = 0
    points_allowed = 0
    home_points_scored = 0
    away_points_scored = 0
    home_points_allowed = 0
    away_points_allowed = 0
    for game in filtered:
        if game["homeTeamId"] == team_id:
            points_scored += game["homeScore"]
            points_allowed += game["awayScore"]
            home_points_scored += game["homeScore"]
            home_points_allowed += game["awayScore"]
            if game["homeScore"] > game["awayScore"]:
                wins += 1
                home_wins +=1
            elif game["homeScore"] < game["awayScore"]:
                losses += 1
                home_losses += 1
            else:
                ties +=1 
                home_ties += 1
        elif game["awayTeamId"] == team_id:
            points_scored += game["awayScore"]
            points_allowed += game["homeScore"]
            away_points_scored += game["awayScore"]
            away_points_allowed += game["homeScore"]
            if game["awayScore"] > game["homeScore"]:
                wins += 1
                away_wins +=1
            elif game["awayScore"] < game["homeScore"]:
                losses += 1
                away_losses += 1
            else:
                ties +=1 
                away_ties += 1

    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "home_wins": home_wins,
        "away_wins": away_wins,
        "home_losses": home_losses,
        "away_losses": away_losses,
        "home_ties": home_ties,
        "away_ties": away_ties,
        "points_scored": points_scored,
        "points_allowed": points_allowed,
        "home_points_scored": home_points_scored,
        "away_points_scored": away_points_scored,
        "home_points_allowed": home_points_allowed,
        "away_points_allowed": away_points_allowed,
        "point_differential": points_scored - points_allowed,
        "avg_margin": (points_scored - points_allowed) / len(filtered),
        "ppg": points_scored / len(filtered),
        "points_allowed_per_game": points_allowed / len(filtered),
        "win_pct": wins / len(filtered),
        "games_played": len(filtered)
    }   



# Stats to track per window:
#   - win%, ppg, points_allowed_per_game, point_diff, avg_margin
# FUNCTION 2 — get_season_stats(team_id, games, season_id)
# Returns a team's full season aggregates for a given season
# Used as a fallback when rolling window doesn't have enough games yet
# Same stats as above but over the full season

def get_season_stats(team_id, games, season_id):
    filtered = []
    for game in games:
        if not game["completed"]:
            continue
        if game["season"] == season_id:
            if game["homeTeamId"] == team_id or game["awayTeamId"] == team_id:
                filtered.append(game)
    # Sort by week ascending for chronological order
    # lambda x: x['week'] == "for each item x in the list, use its week value to sort"
    filtered.sort(key=lambda x: x['week'])
    if len(filtered) < config.MIN_GAMES_PLAYED:
        return None
    wins = 0
    losses = 0
    home_wins = 0
    away_wins = 0
    home_losses = 0
    away_losses = 0
    ties = 0
    home_ties = 0
    away_ties = 0
    points_scored = 0
    points_allowed = 0
    home_points_scored = 0
    away_points_scored = 0
    home_points_allowed = 0
    away_points_allowed = 0
    for game in filtered:
        if game["homeTeamId"] == team_id:
            points_scored += game["homeScore"]
            points_allowed += game["awayScore"]
            home_points_scored += game["homeScore"]
            home_points_allowed += game["awayScore"]
            if game["homeScore"] > game["awayScore"]:
                wins += 1
                home_wins +=1
            elif game["homeScore"] < game["awayScore"]:
                losses += 1
                home_losses += 1
            else:
                ties +=1 
                home_ties += 1
        elif game["awayTeamId"] == team_id:
            points_scored += game["awayScore"]
            points_allowed += game["homeScore"]
            away_points_scored += game["awayScore"]
            away_points_allowed += game["homeScore"]
            if game["awayScore"] > game["homeScore"]:
                wins += 1
                away_wins +=1
            elif game["awayScore"] < game["homeScore"]:
                losses += 1
                away_losses += 1
            else:
                ties +=1 
                away_ties += 1

    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "home_wins": home_wins,
        "away_wins": away_wins,
        "home_losses": home_losses,
        "away_losses": away_losses,
        "home_ties": home_ties,
        "away_ties": away_ties,
        "points_scored": points_scored,
        "points_allowed": points_allowed,
        "home_points_scored": home_points_scored,
        "away_points_scored": away_points_scored,
        "home_points_allowed": home_points_allowed,
        "away_points_allowed": away_points_allowed,
        "point_differential": points_scored - points_allowed,
        "avg_margin": (points_scored - points_allowed) / len(filtered),
        "ppg": points_scored / len(filtered),
        "points_allowed_per_game": points_allowed / len(filtered),
        "win_pct": wins / len(filtered),
        "games_played": len(filtered)
    }   

# Test
# if __name__ == "__main__":
#     games = load_games()

#     print("--- get_rolling_stats ---")
#     result = get_rolling_stats("dal", games, as_of_week=5, season_id=1)
#     print(result)

#     print("--- get_season_stats ---")
#     result2 = get_season_stats("dal", games, season_id=1)
#     print(result2)






# Nudge: filter games to only include completed games for team_id
#        before as_of_week in season_id first, then take the last N
# Nudge: sort the filtered games by week before taking the window
#        otherwise you might get the wrong N games
# Nudge: point_diff and avg_margin are different —
#        point_diff is total, avg_margin is per game
#
# VERIFICATION
# Pick a team and a specific week and manually verify the output
# matches what you'd expect from the standings data