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


def simulate_game(home_id, away_id, games, team_stats_map, season_id, elo_ratings):
    features = build_matchup_features(
        home_id, away_id, games, team_stats_map,
        as_of_week=18, season_id=season_id,
        elo_ratings=elo_ratings, is_playoff=True
    )
    prediction = predict_game(features)
    score = predict_score(features["home_rating"], features["away_rating"])
    return {
        "home_id": home_id,
        "away_id": away_id,
        "winner": prediction["winner"],
        "loser": away_id if prediction["winner"] == home_id else home_id,
        "home_win_prob": round(prediction["home_win_prob"], 3),
        "away_win_prob": round(prediction["away_win_prob"], 3),
        "confidence": round(prediction["confidence"], 3),
        "predicted_home_score": score["home_score"],
        "predicted_away_score": score["away_score"],
    }


def simulate_bracket(seeds, games, team_stats_map, season_id, elo_ratings):
    bracket = {}

    for conf in config.CONFERENCES:
        conf_seeds = seeds[conf]
        if len(conf_seeds) < 6:
            continue

        s1, s2, s3, s4, s5, s6 = conf_seeds

        # Wildcard — 3 hosts 6, 4 hosts 5
        wc1 = simulate_game(s3, s6, games, team_stats_map, season_id, elo_ratings)
        wc2 = simulate_game(s4, s5, games, team_stats_map, season_id, elo_ratings)

        wc1_winner = wc1["winner"]
        wc2_winner = wc2["winner"]

        # Divisional — 1 hosts lowest remaining seed, 2 hosts highest remaining seed
        # remaining seeds after wildcard — sort by original seed position
        remaining = []
        for team in [wc1_winner, wc2_winner]:
            seed_num = conf_seeds.index(team) + 1
            remaining.append((seed_num, team))
        remaining.sort(key=lambda x: x[0])

        lowest_seed = remaining[-1][1]
        highest_seed = remaining[0][1]

        div1 = simulate_game(s1, lowest_seed, games, team_stats_map, season_id, elo_ratings)
        div2 = simulate_game(s2, highest_seed, games, team_stats_map, season_id, elo_ratings)

        div1_winner = div1["winner"]
        div2_winner = div2["winner"]

        # Conference championship
        # Higher seed hosts — check original seed positions
        div1_seed = conf_seeds.index(div1_winner) + 1
        div2_seed = conf_seeds.index(div2_winner) + 1

        if div1_seed <= div2_seed:
            conf_game = simulate_game(div1_winner, div2_winner, games, team_stats_map, season_id, elo_ratings)
        else:
            conf_game = simulate_game(div2_winner, div1_winner, games, team_stats_map, season_id, elo_ratings)

        bracket[conf] = {
            "seeds": conf_seeds,
            "wildcard": [wc1, wc2],
            "divisional": [div1, div2],
            "conference": conf_game,
            "champion": conf_game["winner"],
        }

    # Super Bowl
    if "AFC" in bracket and "NFC" in bracket:
        afc_champ = bracket["AFC"]["champion"]
        nfc_champ = bracket["NFC"]["champion"]
        # neutral site — use AFC champ as home by convention
        sb = simulate_game(afc_champ, nfc_champ, games, team_stats_map, season_id, elo_ratings)
        bracket["superbowl"] = sb
        bracket["champion"] = sb["winner"]

    return bracket


def print_bracket(bracket):
    for conf in config.CONFERENCES:
        if conf not in bracket:
            continue
        b = bracket[conf]
        print(f"\n{'='*40}")
        print(f"{conf} BRACKET")
        print(f"{'='*40}")

        print("\nWILDCARD")
        for game in b["wildcard"]:
            h, a = config.ABBR[game["home_id"]], config.ABBR[game["away_id"]]
            w = config.ABBR[game["winner"]]
            prob = game["home_win_prob"] if game["winner"] == game["home_id"] else game["away_win_prob"]
            print(f"  {h} vs {a} → {w} wins ({round(prob*100)}%)")

        print("\nDIVISIONAL")
        for game in b["divisional"]:
            h, a = config.ABBR[game["home_id"]], config.ABBR[game["away_id"]]
            w = config.ABBR[game["winner"]]
            prob = game["home_win_prob"] if game["winner"] == game["home_id"] else game["away_win_prob"]
            print(f"  {h} vs {a} → {w} wins ({round(prob*100)}%)")

        print(f"\n{conf} CHAMPIONSHIP")
        game = b["conference"]
        h, a = config.ABBR[game["home_id"]], config.ABBR[game["away_id"]]
        w = config.ABBR[game["winner"]]
        prob = game["home_win_prob"] if game["winner"] == game["home_id"] else game["away_win_prob"]
        print(f"  {h} vs {a} → {w} wins ({round(prob*100)}%)")
        print(f"  {conf} CHAMPION: {config.ABBR[b['champion']]}")

    if "superbowl" in bracket:
        print(f"\n{'='*40}")
        print("SUPER BOWL")
        print(f"{'='*40}")
        game = bracket["superbowl"]
        h, a = config.ABBR[game["home_id"]], config.ABBR[game["away_id"]]
        w = config.ABBR[game["winner"]]
        prob = game["home_win_prob"] if game["winner"] == game["home_id"] else game["away_win_prob"]
        print(f"  {h} vs {a} → {w} wins ({round(prob*100)}%)")
        print(f"\n  SUPER BOWL CHAMPION: {config.ABBR[bracket['champion']]}")


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
    standings = build_standings(results)
    seeds = get_playoff_seeds(standings, games)
    bracket = simulate_bracket(seeds, games, team_stats_map, season_id=8, elo_ratings=elo_ratings)
    print_bracket(bracket)