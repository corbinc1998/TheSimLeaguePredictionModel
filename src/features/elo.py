import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games
import config


def is_neutral_site(game):
    """Super Bowl (and any other configured week) is played at a neutral site."""
    return bool(game.get("isPlayoff")) and game.get("week") in config.NEUTRAL_SITE_WEEKS


def expected_score(elo_gap):
    """Standard Elo expectation for the side that is elo_gap points stronger."""
    return 1 / (1 + 10 ** (-elo_gap / 400))


def regress_to_mean(elo_ratings):
    """
    Offseason step: pull every team part of the way back toward the mean.
    Same idea as FiveThirtyEight's NFL Elo, which reverts one-third per season.
    """
    mean = config.ELO_INITIAL
    keep = 1 - config.ELO_SEASON_REGRESSION
    return {team_id: mean + keep * (rating - mean) for team_id, rating in elo_ratings.items()}


def compute_elo_ratings(games, as_of_season=None):
    """
    Walk completed games in order and return (ratings, history).

    as_of_season: the season the ratings will be used for. If that season
    has no completed games yet (preseason / Week 1), the offseason
    regression is still applied so Week 1 predictions start from
    regressed ratings. Defaults to the latest season present in games,
    which is right for the live pipeline once the new schedule is loaded.
    """
    elo_ratings = {team_id: config.ELO_INITIAL for team_id in config.TEAM_IDS}
    elo_history = []

    completed = [g for g in games if g.get("completed", False)]
    completed.sort(key=lambda x: (x["season"], x["week"]))

    current_season = None
    for game in completed:
        if current_season is not None and game["season"] != current_season:
            for _ in range(game["season"] - current_season):
                elo_ratings = regress_to_mean(elo_ratings)
        current_season = game["season"]

        k = config.ELO_K_PLAYOFF if game.get("isPlayoff") else config.ELO_K_FACTOR
        home_team = game["homeTeamId"]
        away_team = game["awayTeamId"]

        # Same home-field adjustment as get_win_probability, so the update
        # and the prediction agree on what "expected" means
        hfa = 0 if is_neutral_site(game) else config.ELO_HOME_ADVANTAGE
        expected_home = expected_score(elo_ratings[home_team] + hfa - elo_ratings[away_team])
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
            "ratings": dict(elo_ratings)  # copy of ratings after this game
        })

    if as_of_season is None:
        seasons = [g["season"] for g in games if g.get("season") is not None]
        as_of_season = max(seasons) if seasons else current_season

    if current_season is not None and as_of_season is not None and as_of_season > current_season:
        for _ in range(as_of_season - current_season):
            elo_ratings = regress_to_mean(elo_ratings)

    return elo_ratings, elo_history


def get_win_probability(team_a_elo, team_b_elo, is_home, neutral=False):
    elo_gap = team_a_elo - team_b_elo
    if not neutral:
        elo_gap += config.ELO_HOME_ADVANTAGE if is_home else -config.ELO_HOME_ADVANTAGE
    return expected_score(elo_gap)


def get_best_wins(team_id, games, elo_history):
    history_by_game = {}
    for snapshot in elo_history:
        history_by_game[snapshot["game_id"]] = snapshot
    wins = []
    for game in games:
        if not game.get("completed", False):
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
#     print("\n--- get_win_probability ---")
#     print(f"Bears vs Ravens (Bears at home): {round(get_win_probability(ratings['chi'], ratings['bal'], True), 3)}")
#     print("\n--- get_best_wins ---")
#     for win in get_best_wins("chi", games, history):
#         print(f"S{win['season']} W{win['week']} vs {win['opponent_id'].upper()} ({round(win['opponent_elo'], 1)}) - {win['score']}")