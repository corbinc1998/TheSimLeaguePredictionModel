import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.loader import load_games, load_team_stats_map
from src.features.elo import compute_elo_ratings
import config


def build_standings(results):
    standings = {tid: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "pd": 0}
                 for tid in config.TEAM_IDS}

    for game in results:
        h = game["homeTeamId"]
        a = game["awayTeamId"]
        if h not in standings or a not in standings:
            continue

        # Explicit None checks: a projected score of 0 must not fall through
        hs = game.get("predicted_home_score")
        if hs is None:
            hs = game.get("homeScore")
        as_ = game.get("predicted_away_score")
        if as_ is None:
            as_ = game.get("awayScore")

        if hs is None or as_ is None:
            continue

        standings[h]["pf"] += hs
        standings[h]["pa"] += as_
        standings[h]["pd"] += hs - as_
        standings[a]["pf"] += as_
        standings[a]["pa"] += hs
        standings[a]["pd"] += as_ - hs

        if hs > as_:
            standings[h]["w"] += 1
            standings[a]["l"] += 1
        elif as_ > hs:
            standings[a]["w"] += 1
            standings[h]["l"] += 1
        else:
            standings[h]["t"] += 1
            standings[a]["t"] += 1

    for tid in standings:
        g = standings[tid]["w"] + standings[tid]["l"] + standings[tid]["t"]
        standings[tid]["win_pct"] = round((standings[tid]["w"] + standings[tid]["t"] * 0.5) / g, 3) if g > 0 else 0

    return standings


def build_division_standings(standings):
    result = {}
    for tid, rec in standings.items():
        conf = config.TEAMS[tid]["conference"]
        div = config.TEAMS[tid]["division"]
        if conf not in result:
            result[conf] = {}
        if div not in result[conf]:
            result[conf][div] = []
        result[conf][div].append({"team_id": tid, **rec})

    for conf in result:
        for div in result[conf]:
            result[conf][div].sort(key=lambda x: (-x["win_pct"], -x["pd"]))

    return result


def get_playoff_seeds(standings, games):
    seeds = {}

    for conf in config.CONFERENCES:
        div_winners = []
        wild_cards = []

        for div in config.DIVISIONS:
            div_teams = [
                {"team_id": tid, **rec}
                for tid, rec in standings.items()
                if config.TEAMS[tid]["conference"] == conf and config.TEAMS[tid]["division"] == div
            ]
            div_teams.sort(key=lambda x: (-x["win_pct"], -x["pd"]))
            if div_teams:
                div_winners.append(div_teams[0])
                wild_cards.extend(div_teams[1:])

        div_winners.sort(key=lambda x: (-x["win_pct"], -x["pd"]))
        wild_cards.sort(key=lambda x: (-x["win_pct"], -x["pd"]))

        conf_seeds = div_winners + wild_cards[:2]
        seeds[conf] = [t["team_id"] for t in conf_seeds[:6]]

    return seeds


if __name__ == "__main__":
    # Deterministic "favorite always wins" standings. For realistic
    # projections use src/simulation/monte_carlo.py (see pipeline.py).
    from src.simulation.season import predict_season

    games = load_games()
    season_id = max(g["season"] for g in games)
    elo_ratings, elo_history = compute_elo_ratings(games, as_of_season=season_id)
    team_stats_map = load_team_stats_map()

    results = predict_season(games, team_stats_map, season_id=season_id, current_week=1, elo_ratings=elo_ratings)
    standings = build_standings(results)
    division_standings = build_division_standings(standings)
    seeds = get_playoff_seeds(standings, games)

    print(f"\n=== PROJECTED S{season_id} STANDINGS (favorite wins every game) ===")
    for conf in config.CONFERENCES:
        print(f"\n{conf}")
        for div in config.DIVISIONS:
            if div in division_standings.get(conf, {}):
                print(f"  {div}")
                for team in division_standings[conf][div]:
                    print(f"    {config.ABBR[team['team_id']]:<5} {team['w']}-{team['l']}-{team['t']}  PD: {team['pd']:+}")

    print("\n=== PROJECTED PLAYOFF SEEDS ===")
    for conf in config.CONFERENCES:
        print(f"\n{conf}")
        for i, tid in enumerate(seeds[conf]):
            print(f"  {i+1}. {config.ABBR[tid]} - {standings[tid]['w']}-{standings[tid]['l']}-{standings[tid]['t']}")