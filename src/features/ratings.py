import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data.loader import load_games, load_team_stats_map
import config
from src.features import rolling, playoff, splits, h2h, elo


def get_prior_season_box_stats(team_stats, season_id):
    """
    Most recent season_by_season entry strictly BEFORE season_id.

    Box-score stats are entered by hand after a season is simmed, so the
    entry for season_id itself contains that whole season's results.
    Using it while that season is being predicted leaks the future.
    """
    if not team_stats or "season_by_season" not in team_stats:
        return None
    earlier = [int(s) for s in team_stats["season_by_season"] if int(s) < season_id]
    if not earlier:
        return None
    return team_stats["season_by_season"][str(max(earlier))]


def box_stats_delta(s):
    """Rating points above/below 50 from one season of box-score stats."""
    delta = 0.0
    delta += (s["offense"]["ppg"] - config.STAT_BASELINES["ppg"]) * config.STAT_WEIGHTS["ppg"]
    delta += (config.STAT_BASELINES["points_allowed"] - s["defense"]["points_allowed"] / 17) * config.STAT_WEIGHTS["points_allowed"]
    delta += (s["turnovers"]["differential"] - config.STAT_BASELINES["turnover_diff"]) * config.STAT_WEIGHTS["turnover_diff"]
    delta += (s["efficiency"]["redzone_td_pct"] * 100 - config.STAT_BASELINES["redzone_td_pct"]) * config.STAT_WEIGHTS["redzone_td_pct"]
    delta += (s["efficiency"]["third_down_pct"] - config.STAT_BASELINES["third_down_pct"]) * config.STAT_WEIGHTS["third_down_pct"]
    return delta


def results_delta(stats):
    """Rating points above/below 50 from game results (scoring only)."""
    delta = 0.0
    delta += (stats["ppg"] - config.STAT_BASELINES["ppg"]) * config.STAT_WEIGHTS["ppg"]
    delta += (config.STAT_BASELINES["points_allowed"] - stats["points_allowed_per_game"]) * config.STAT_WEIGHTS["points_allowed"]
    return delta


def prior_season_delta(team_id, games, team_stats, season_id):
    """Last season's strength: box-score stats if entered, else last season's results."""
    box = get_prior_season_box_stats(team_stats, season_id)
    if box is not None:
        return box_stats_delta(box)
    last_season = rolling.get_season_stats(team_id, games, season_id - 1)
    if last_season:
        return results_delta(last_season)
    return 0.0


def build_team_rating(team_id, games, team_stats, as_of_week, season_id, elo_ratings):
    # Prior season and current season are blended by games played:
    # w = n / (n + k). Early on the prior dominates; by midseason the
    # current season does. Only games before as_of_week are counted.
    prior = prior_season_delta(team_id, games, team_stats, season_id)
    current_stats = rolling.get_season_stats(team_id, games, season_id, before_week=as_of_week)
    if current_stats:
        n = current_stats["games_played"]
        w = n / (n + config.PRIOR_BLEND_K)
        strength = (1 - w) * prior + w * results_delta(current_stats)
    else:
        strength = prior

    base_rating = 50 + strength

    # Rolling as a small supplement for recent form only
    rolling_stats = rolling.get_rolling_stats(team_id, games, as_of_week, season_id)
    if rolling_stats:
        base_rating += results_delta(rolling_stats) * config.ROLLING_FORM_WEIGHT

    # Elo: ELO_RATING_WEIGHT rating points per 100 Elo points above average.
    # (The old (elo - 1500) / 400 * 0.3 scaling made Elo worth ~0.1 points,
    # so it had no effect at all.)
    if team_id in elo_ratings:
        base_rating += (elo_ratings[team_id] - config.ELO_INITIAL) / 100 * config.ELO_RATING_WEIGHT

    clutch = playoff.get_playoff_clutch(team_id, games)
    if clutch:
        base_rating += clutch * config.WEIGHTS["playoff_clutch"]

    # Compress rating toward 50 to reduce extreme predictions
    base_rating = 50 + (base_rating - 50) * 0.5
    return max(config.RATING_MIN, min(config.RATING_MAX, base_rating))


def build_matchup_features(home_id, away_id, games, team_stats_map, as_of_week, season_id,
                           elo_ratings, is_playoff=False, is_neutral=False):
    home_stats = team_stats_map.get(home_id)
    away_stats = team_stats_map.get(away_id)

    home_rating = build_team_rating(home_id, games, home_stats, as_of_week, season_id, elo_ratings)
    away_rating = build_team_rating(away_id, games, away_stats, as_of_week, season_id, elo_ratings)

    away_splits = splits.get_home_away_splits(away_id, games)

    home_boost = splits.get_home_boost(home_id, games)
    # Away team's average point differential on the road.
    # Positive means a strong road team, which should LOWER the home edge.
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
        "is_neutral":           is_neutral,
    }


# Testing
if __name__ == "__main__":
    games = load_games()
    season = max(g["season"] for g in games)
    elo_ratings, elo_history = elo.compute_elo_ratings(games, as_of_season=season)
    team_stats_map = load_team_stats_map()

    print(f"\n--- All Team Ratings (Season {season}, Week 1) ---")
    all_ratings = {
        tid: build_team_rating(tid, games, team_stats_map[tid], as_of_week=1,
                               season_id=season, elo_ratings=elo_ratings)
        for tid in config.TEAM_IDS
    }
    for team_id, rating in sorted(all_ratings.items(), key=lambda x: -x[1]):
        print(f"{config.ABBR[team_id]:<5} {round(rating, 1)}")

    print("\n--- Matchup Features: Bears vs Packers ---")
    features = build_matchup_features("chi", "gb", games, team_stats_map, as_of_week=1,
                                      season_id=season, elo_ratings=elo_ratings)
    for k, v in features.items():
        print(f"  {k}: {v}")