import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

def sigmoid(x):
    return 1 / (1 + math.pow(math.e, -x))


def predict_game(features):
    prediction = {
        "home_win_prob": 0,
        "away_win_prob": 0,
        "winner": "",
        "confidence": 0
    }
    edge = (
        features["rating_gap"]
        + features["home_boost"] * config.WEIGHTS["home_boost"]
        + features["away_road_factor"] * config.WEIGHTS["away_factor"]
        + (features["h2h_edge"] - 0.5) * config.WEIGHTS["h2h_edge"]
        + features["h2h_margin"] * config.WEIGHTS["h2h_margin"]
        + features["playoff_clutch_diff"] * config.WEIGHTS["playoff_clutch"]
        + config.HOME_FIELD_ADVANTAGE
    )
    home_win_prob = sigmoid(edge * config.LOGISTIC_SCALE)
    prediction["home_win_prob"] = home_win_prob
    prediction["away_win_prob"] = 1 - home_win_prob
    prediction["winner"] = features["home_id"] if home_win_prob >= 0.5 else features["away_id"]
    prediction["confidence"] = abs(home_win_prob - 0.5) * 2
    return prediction

def predict_score(home_rating, away_rating):
    baseline = config.STAT_BASELINES["ppg"]
    home_score = round(baseline + (home_rating - 50) * 0.5)
    away_score = round(baseline + (away_rating - 50) * 0.5)
    return {"home_score": home_score, "away_score": away_score}



# Testing
# if __name__ == "__main__":
#     test_features = {
#         "home_id": "chi", "away_id": "gb",
#         "home_rating": 59.68, "away_rating": 38.51,
#         "rating_gap": 21.17, "home_boost": 2.13,
#         "away_road_factor": 2.16, "h2h_edge": 0.49,
#         "h2h_margin": -4.47, "playoff_clutch_diff": 0.0,
#         "is_playoff": False
#     }
#     print(predict_game(test_features))
#     print(predict_score(59.68, 38.51))