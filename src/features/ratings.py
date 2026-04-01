import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games, load_team_stats
import config
from src.features import rolling, playoff, splits, h2h, elo

def build_team_rating(team_id, games, team_stats, as_of_week, season_id, elo_ratings):
    season_stats = rolling.get_season_stats(team_id, games, season_id)
    rolling_stats = rolling.get_rolling_stats(team_id, games, as_of_week, season_id)
    clutch = playoff.get_playoff_clutch(team_id, games)
    base_rating = 50


    # Use team_stats JSON as primary source
    # Fall back to season_stats from rolling only if team_stats unavailable
    if team_stats and "season_by_season" in team_stats:
        available = sorted(team_stats["season_by_season"].keys(), key=lambda x: int(x))
        best_season = str(season_id) if str(season_id) in team_stats["season_by_season"] else available[-1] if available else None
        if best_season:
            s = team_stats["season_by_season"][best_season]
            base_rating += (s["offense"]["ppg"] - config.STAT_BASELINES["ppg"]) * config.STAT_WEIGHTS["ppg"]
            base_rating += (config.STAT_BASELINES["points_allowed"] - s["defense"]["points_allowed"] / 17) * config.STAT_WEIGHTS["points_allowed"]
            base_rating += (s["turnovers"]["differential"] - config.STAT_BASELINES["turnover_diff"]) * config.STAT_WEIGHTS["turnover_diff"]
            base_rating += (s["efficiency"]["redzone_td_pct"] * 100 - config.STAT_BASELINES["redzone_td_pct"]) * config.STAT_WEIGHTS["redzone_td_pct"]
            base_rating += (s["efficiency"]["third_down_pct"] - config.STAT_BASELINES["third_down_pct"]) * config.STAT_WEIGHTS["third_down_pct"]
    elif season_stats:
        base_rating += (season_stats["ppg"] - config.STAT_BASELINES["ppg"]) * config.STAT_WEIGHTS["ppg"]
        base_rating += (config.STAT_BASELINES["points_allowed"] - season_stats["points_allowed_per_game"]) * config.STAT_WEIGHTS["points_allowed"]

    # Rolling as a small supplement for recent form only
    if rolling_stats:
        base_rating += (rolling_stats["ppg"] - config.STAT_BASELINES["ppg"]) * config.STAT_WEIGHTS["ppg"] * 0.2
        base_rating += (config.STAT_BASELINES["points_allowed"] - rolling_stats["points_allowed_per_game"]) * config.STAT_WEIGHTS["points_allowed"] * 0.2

    if team_id in elo_ratings:
        base_rating += (elo_ratings[team_id] - 1500) / 400 * config.ELO_RATING_WEIGHT

    if clutch:
        base_rating += clutch * config.WEIGHTS["playoff_clutch"]

    # Compress rating toward 50 to reduce extreme predictions
    base_rating = 50 + (base_rating - 50) * 0.5
    return max(config.RATING_MIN, min(config.RATING_MAX, base_rating))


def build_matchup_features(home_id, away_id, games, team_stats_map, as_of_week, season_id, elo_ratings, is_playoff=False):
    home_stats = team_stats_map.get(home_id)
    away_stats = team_stats_map.get(away_id)

    home_rating = build_team_rating(home_id, games, home_stats, as_of_week, season_id, elo_ratings)
    away_rating = build_team_rating(away_id, games, away_stats, as_of_week, season_id, elo_ratings)

    home_splits = splits.get_home_away_splits(home_id, games)
    away_splits = splits.get_home_away_splits(away_id, games)

    home_boost = splits.get_home_boost(home_id, games)
    away_road_factor = away_splits["away"]["point_diff"] / away_splits["away"]["games"] if away_splits["away"]["games"] > 0 else 0

    h2h_edge = h2h.get_h2h_record(home_id, away_id, games, season_id)
    h2h_margin = h2h.get_h2h_margin(home_id, away_id, games, season_id)

    if is_playoff:
        home_clutch = playoff.get_playoff_clutch(home_id, games) or 0.0
        away_clutch = playoff.get_playoff_clutch(away_id, games) or 0.0
        playoff_clutch_diff = home_clutch - away_clutch
    else:
        playoff_clutch_diff = 0.0

    return {
        "home_id":              home_id,
        "away_id":              away_id,
        "home_rating":          round(home_rating, 2),
        "away_rating":          round(away_rating, 2),
        "rating_gap":           round(home_rating - away_rating, 2),
        "home_boost":           round(home_boost, 2),
        "away_road_factor":     round(away_road_factor, 2),
        "h2h_edge":             round(h2h_edge, 3),
        "h2h_margin":           round(h2h_margin, 2),
        "playoff_clutch_diff":  round(playoff_clutch_diff, 2),
        "is_playoff":           is_playoff,
    }


# Testing
if __name__ == "__main__":
    games = load_games()
    elo_ratings, elo_history = elo.compute_elo_ratings(games)
    print("\n--- All Team Ratings ---")
    all_ratings = {}
    for team_id in config.TEAM_IDS:
        try:
            team_stats = load_team_stats(team_id)
        except:
            team_stats = None
        rating = build_team_rating(team_id, games, team_stats, as_of_week=22, season_id=7, elo_ratings=elo_ratings)
        all_ratings[team_id] = rating

    for team_id, rating in sorted(all_ratings.items(), key=lambda x: -x[1]):
        print(f"{config.ABBR[team_id]:<5} {round(rating, 1)}")
    # load all team stats into a map
    team_stats_map = {}
    for tid in config.TEAM_IDS:
        try:
            team_stats_map[tid] = load_team_stats(tid)
        except:
            team_stats_map[tid] = None

    print("\n--- Matchup Features: Bears vs Packers ---")
    features = build_matchup_features("chi", "gb", games, team_stats_map, as_of_week=22, season_id=7, elo_ratings=elo_ratings, is_playoff=False)
    for k, v in features.items():
        print(f"  {k}: {v}")
