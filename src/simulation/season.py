import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.loader import load_games, load_team_stats_map
from src.features.ratings import build_matchup_features
from src.features.elo import compute_elo_ratings
from src.model.predict import predict_game, predict_score
import config


def predict_season(games, team_stats_map, season_id, current_week, elo_ratings):
    """
    One row per regular-season game. Completed games carry their real score
    (predicted=False); unplayed games carry a win probability and a projected
    score (predicted=True).

    current_week is kept for callers and logging; which games count as played
    comes from each game's "completed" flag.

    Accuracy is NOT measured here: a completed game's "winner" is the actual
    winner, so comparing it to the result always scores 100%. Use
    src/evaluation/backtest.py, which predicts each game before its result.
    """
    results = []
    season_games = [g for g in games if g.get("season") == season_id and not g.get("isPlayoff")]

    for game in season_games:
        if game.get("completed"):
            results.append({
                **game,
                "predicted": False,
                "home_win_prob": 1.0 if game["homeScore"] > game["awayScore"] else 0.0,
                "winner": game["homeTeamId"] if game["homeScore"] > game["awayScore"] else game["awayTeamId"],
                "confidence": 1.0,
                "predicted_home_score": game["homeScore"],
                "predicted_away_score": game["awayScore"],
            })
        else:
            features = build_matchup_features(
                game["homeTeamId"], game["awayTeamId"],
                games, team_stats_map,
                as_of_week=game["week"],
                season_id=season_id,
                elo_ratings=elo_ratings,
                is_playoff=False
            )
            prediction = predict_game(features)
            score = predict_score(features)
            results.append({
                **game,
                "predicted": True,
                "home_win_prob": round(prediction["home_win_prob"], 3),
                "away_win_prob": round(prediction["away_win_prob"], 3),
                "winner": prediction["winner"],
                "confidence": round(prediction["confidence"], 3),
                "predicted_home_score": score["home_score"],
                "predicted_away_score": score["away_score"],
            })

    return results


def get_season_predictions(games, team_stats_map, season_id, current_week, elo_ratings):
    all_results = predict_season(games, team_stats_map, season_id, current_week, elo_ratings)
    return [g for g in all_results if g.get("predicted")]


if __name__ == "__main__":
    games = load_games()
    season_id = max(g["season"] for g in games)
    elo_ratings, elo_history = compute_elo_ratings(games, as_of_season=season_id)
    team_stats_map = load_team_stats_map()

    preds = get_season_predictions(games, team_stats_map, season_id=season_id, current_week=1, elo_ratings=elo_ratings)
    print(f"Season {season_id}: {len(preds)} unplayed games")
    print("\nSample predictions (first 5 unplayed games):")
    for g in preds[:5]:
        print(f"  W{g['week']} {config.ABBR[g['homeTeamId']]} vs {config.ABBR[g['awayTeamId']]} - "
              f"{g['winner'].upper()} ({round(g['home_win_prob']*100)}% home)")