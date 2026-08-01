import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.loader import load_games, load_team_stats
from src.features.elo import compute_elo_ratings
from src.features.ratings import build_matchup_features
from src.model.predict import predict_game, predict_score
from src.simulation.season import predict_season
from src.simulation.standings import build_standings, get_playoff_seeds
import config


def get_actual_result(home_id, away_id, week, games):
    """
    Return actual winner if a completed playoff game exists for these teams.
    Matches on team pair regardless of home/away order, and accepts week=None
    to search across all playoff weeks (used as fallback).
    """
    teams = {home_id, away_id}
    for g in games:
        if not g.get("isPlayoff") or not g.get("completed"):
            continue
        if week is not None and g.get("week") != week:
            continue
        if {g.get("homeTeamId"), g.get("awayTeamId")} != teams:
            continue
        home_score = g.get("homeScore")
        away_score = g.get("awayScore")
        if home_score is None or away_score is None:
            continue
        actual_home = g["homeTeamId"]
        actual_away = g["awayTeamId"]
        if home_score > away_score:
            winner = actual_home
            loser  = actual_away
        else:
            winner = actual_away
            loser  = actual_home
        return {
            "home_id":              home_id,
            "away_id":              away_id,
            "winner":               winner,
            "loser":                loser,
            "home_win_prob":        None,
            "away_win_prob":        None,
            "confidence":           None,
            "predicted_home_score": home_score,
            "predicted_away_score": away_score,
            "actual":               True,
        }
    return None


def simulate_game(home_id, away_id, games, team_stats_map, season_id, elo_ratings, week=None):
    """
    Simulate or return the actual result of a playoff game.
    Tries exact week match first, then falls back to any completed
    playoff game between these two teams (handles week numbering mismatches).
    """
    if week is not None:
        actual = get_actual_result(home_id, away_id, week, games)
        if actual:
            return actual
        # Fallback: search all playoff weeks in case week number is off
        actual = get_actual_result(home_id, away_id, None, games)
        if actual:
            return actual

    features = build_matchup_features(
        home_id, away_id, games, team_stats_map,
        as_of_week=18, season_id=season_id,
        elo_ratings=elo_ratings, is_playoff=True
    )
    prediction = predict_game(features)
    score = predict_score(features["home_rating"], features["away_rating"])
    return {
        "home_id":              home_id,
        "away_id":              away_id,
        "winner":               prediction["winner"],
        "loser":                away_id if prediction["winner"] == home_id else home_id,
        "home_win_prob":        round(prediction["home_win_prob"], 3),
        "away_win_prob":        round(prediction["away_win_prob"], 3),
        "confidence":           round(prediction["confidence"], 3),
        "predicted_home_score": score["home_score"],
        "predicted_away_score": score["away_score"],
    }


def _get_seed(team, conf_seeds):
    """
    Return the seed number (1-based) for a team.
    Returns 99 if not found so eliminated teams sort to the bottom.
    """
    try:
        return conf_seeds.index(team) + 1
    except ValueError:
        return 99


def _host_then_visitor(team_a, team_b, conf_seeds):
    """
    Return (home, away) where the better seed hosts.
    """
    seed_a = _get_seed(team_a, conf_seeds)
    seed_b = _get_seed(team_b, conf_seeds)
    if seed_a <= seed_b:
        return team_a, team_b
    return team_b, team_a


def simulate_bracket(seeds, games, team_stats_map, season_id, elo_ratings):
    bracket = {}

    # Flatten games if needed
    all_games = []
    for season_data in (games.values() if isinstance(games, dict) else []):
        all_games.extend(season_data.get("games", []))
    flat_games = all_games if all_games else games

    for conf in config.CONFERENCES:
        conf_seeds = seeds[conf]
        if len(conf_seeds) < 6:
            continue

        s1, s2, s3, s4, s5, s6 = conf_seeds

        # ── Wild Card (week 18) ───────────────────────────────────────────────
        # 3 vs 6, 4 vs 5 — higher seed hosts
        wc1 = simulate_game(s3, s6, flat_games, team_stats_map, season_id, elo_ratings, week=18)
        wc2 = simulate_game(s4, s5, flat_games, team_stats_map, season_id, elo_ratings, week=18)

        wc1_winner = wc1["winner"]
        wc2_winner = wc2["winner"]

        # Verify winners are valid — guard against eliminated team bleed-through
        valid_wc_teams = {s3, s4, s5, s6}
        if wc1_winner not in valid_wc_teams:
            wc1_winner = s3   # fallback to higher seed
        if wc2_winner not in valid_wc_teams:
            wc2_winner = s4

        # ── Divisional (week 19) ─────────────────────────────────────────────
        # Reseed: s1 hosts lowest remaining seed, s2 hosts highest remaining seed
        wc_survivors = sorted(
            [wc1_winner, wc2_winner],
            key=lambda t: _get_seed(t, conf_seeds)
        )
        # wc_survivors[0] = better seed (lower number), [1] = worse seed
        highest_wc = wc_survivors[0]   # better wild card survivor — plays s2
        lowest_wc  = wc_survivors[1]   # worse wild card survivor  — plays s1

        div1 = simulate_game(s1, lowest_wc,  flat_games, team_stats_map, season_id, elo_ratings, week=19)
        div2 = simulate_game(s2, highest_wc, flat_games, team_stats_map, season_id, elo_ratings, week=19)

        div1_winner = div1["winner"]
        div2_winner = div2["winner"]

        # Verify winners came from their respective games
        if div1_winner not in {s1, lowest_wc}:
            div1_winner = s1
        if div2_winner not in {s2, highest_wc}:
            div2_winner = s2

        # ── Conference Championship (week 20) ─────────────────────────────────
        # Better seed hosts — look up original seed for home/away assignment
        conf_home, conf_away = _host_then_visitor(div1_winner, div2_winner, conf_seeds)
        conf_game = simulate_game(
            conf_home, conf_away,
            flat_games, team_stats_map, season_id, elo_ratings, week=20
        )

        # Verify conference champion came from this game
        conf_champ = conf_game["winner"]
        if conf_champ not in {div1_winner, div2_winner}:
            conf_champ = conf_home   # fallback

        bracket[conf] = {
            "seeds":      conf_seeds,
            "wildcard":   [wc1, wc2],
            "divisional": [div1, div2],
            "conference": conf_game,
            "champion":   conf_champ,
        }

    # ── Super Bowl (week 21) ─────────────────────────────────────────────────
    if "AFC" in bracket and "NFC" in bracket:
        afc_champ = bracket["AFC"]["champion"]
        nfc_champ = bracket["NFC"]["champion"]
        # Super Bowl is neutral site — AFC champ listed as home by convention
        sb = simulate_game(
            afc_champ, nfc_champ,
            flat_games, team_stats_map, season_id, elo_ratings, week=21
        )
        bracket["superbowl"] = sb
        bracket["champion"]  = sb["winner"]

    return bracket