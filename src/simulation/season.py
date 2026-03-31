import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.loader import load_games, load_team_stats
from src.features.ratings import build_matchup_features
from src.features.elo import compute_elo_ratings
from src.model.predict import predict_game, predict_score
import config


def predict_season(games, team_stats_map, season_id, current_week, elo_ratings):
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
            score = predict_score(features["home_rating"], features["away_rating"])
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
    elo_ratings, elo_history = compute_elo_ratings(games)

    team_stats_map = {}
    for tid in config.TEAM_IDS:
        try:
            team_stats_map[tid] = load_team_stats(tid)
        except:
            team_stats_map[tid] = None

    results = predict_season(games, team_stats_map, season_id=8, current_week=1, elo_ratings=elo_ratings)

    correct = 0
    total = 0
    for g in results:
        if g.get("completed") and not g.get("predicted"):
            actual_winner = g["homeTeamId"] if g["homeScore"] > g["awayScore"] else g["awayTeamId"]
            if g["winner"] == actual_winner:
                correct += 1
            total += 1

    if total > 0:
        print(f"Season 8 predictions: {correct}/{total} correct ({round(correct/total*100, 1)}%)")
    else:
        print("No completed games to evaluate — showing predictions only")

    print("\nSample predictions (first 5 unplayed games):")
    preds = get_season_predictions(games, team_stats_map, season_id=8, current_week=1, elo_ratings=elo_ratings)
    for g in preds[:5]:
        print(f"  W{g['week']} {config.ABBR[g['homeTeamId']]} vs {config.ABBR[g['awayTeamId']]} — {g['winner'].upper()} wins ({round(g['home_win_prob']*100)}% home)")