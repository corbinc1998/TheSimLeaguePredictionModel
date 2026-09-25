import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def compute_edge(features):
    """
    Home team's edge in rating points. Positive favors the home team.
    Home-field terms are dropped entirely at a neutral site.
    """
    edge = (
        features["rating_gap"]
        + (features["h2h_edge"] - 0.5) * config.WEIGHTS["h2h_edge"]
        + features["h2h_margin"] * config.WEIGHTS["h2h_margin"]
        + features["playoff_clutch_diff"] * config.WEIGHTS["playoff_clutch"]
    )
    if not features.get("is_neutral"):
        edge += (
            features["home_boost"] * config.WEIGHTS["home_boost"]
            # A strong road team makes the home team LESS likely to win
            - features["away_road_factor"] * config.WEIGHTS["away_factor"]
            + config.HOME_FIELD_ADVANTAGE
        )
    return edge


def predict_game(features):
    edge = compute_edge(features)
    home_win_prob = sigmoid(edge * config.LOGISTIC_SCALE)
    return {
        "home_win_prob": home_win_prob,
        "away_win_prob": 1 - home_win_prob,
        "winner": features["home_id"] if home_win_prob >= 0.5 else features["away_id"],
        "confidence": abs(home_win_prob - 0.5) * 2,
        "edge": edge,
    }


def predict_score(features):
    """
    Projected score built from the same edge as the win probability, so the
    projected score always agrees with the predicted winner. The margin is
    POINTS_PER_EDGE points per rating point of edge, split evenly around the
    league-average scoring baseline.
    """
    edge = compute_edge(features)
    margin = edge * config.POINTS_PER_EDGE
    baseline = config.STAT_BASELINES["ppg"]
    home_score = round(baseline + margin / 2)
    away_score = round(baseline - margin / 2)
    if home_score == away_score:
        if edge >= 0:
            home_score += 1
        else:
            away_score += 1
    return {"home_score": home_score, "away_score": away_score}


# Testing
# if __name__ == "__main__":
#     test_features = {
#         "home_id": "chi", "away_id": "gb",
#         "home_rating": 59.68, "away_rating": 38.51,
#         "rating_gap": 21.17, "home_boost": 2.13,
#         "away_road_factor": 2.16, "h2h_edge": 0.49,
#         "h2h_margin": -4.47, "playoff_clutch_diff": 0.0,
#         "is_playoff": False, "is_neutral": False,
#     }
#     print(predict_game(test_features))
#     print(predict_score(test_features))