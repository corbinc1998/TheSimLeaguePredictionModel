"""
Monte Carlo season simulation.

Instead of handing every game to the favorite (which produces 16-0 and 0-16
records), each unplayed game is decided by a random draw against its win
probability, and the whole season plus playoffs is replayed many times.
The output is each team's expected wins and its odds of reaching each
playoff milestone.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import random

import config
from src.features.ratings import build_matchup_features
from src.model.predict import predict_game
from src.simulation.standings import get_playoff_seeds


def _playoff_result_lookup(games, season_id):
    """{frozenset(team pair): winner} for playoff games already played this season."""
    lookup = {}
    for g in games:
        if g["season"] != season_id or not g.get("isPlayoff") or not g.get("completed"):
            continue
        winner = g["homeTeamId"] if g["homeScore"] > g["awayScore"] else g["awayTeamId"]
        lookup[frozenset((g["homeTeamId"], g["awayTeamId"]))] = winner
    return lookup


def _seed_of(team, conf_seeds):
    return conf_seeds.index(team) + 1 if team in conf_seeds else 99


def simulate_season(season_results, games, team_stats_map, season_id, elo_ratings,
                    n_sims=None, seeds_override=None, rng_seed=None):
    """
    season_results: output of season.predict_season (completed games carry
    their real score, unplayed games carry home_win_prob and a projected score).

    seeds_override: real playoff seeds once the regular season is over
    (the pipeline's hardcoded seeds), so playoff odds use the actual bracket.

    Returns {team_id: {expected_wins, playoff_pct, bye_pct, conf_title_pct, sb_win_pct}}.
    """
    n_sims = n_sims or config.MONTE_CARLO_SIMS
    rng = random.Random(rng_seed)

    # Fixed part of the season: games already played
    base = {tid: {"w": 0, "l": 0, "t": 0, "pd": 0} for tid in config.TEAM_IDS}
    unplayed = []
    for g in season_results:
        h, a = g["homeTeamId"], g["awayTeamId"]
        if g.get("completed") and not g.get("predicted"):
            hs, as_ = g["homeScore"], g["awayScore"]
            base[h]["pd"] += hs - as_
            base[a]["pd"] += as_ - hs
            if hs > as_:
                base[h]["w"] += 1; base[a]["l"] += 1
            elif as_ > hs:
                base[a]["w"] += 1; base[h]["l"] += 1
            else:
                base[h]["t"] += 1; base[a]["t"] += 1
        else:
            margin = abs(g["predicted_home_score"] - g["predicted_away_score"]) or 1
            unplayed.append((h, a, g["home_win_prob"], margin))

    played_playoffs = _playoff_result_lookup(games, season_id)
    prob_cache = {}

    def playoff_home_prob(home, away, neutral):
        key = (home, away, neutral)
        if key not in prob_cache:
            features = build_matchup_features(
                home, away, games, team_stats_map, as_of_week=18, season_id=season_id,
                elo_ratings=elo_ratings, is_playoff=True, is_neutral=neutral,
            )
            prob_cache[key] = predict_game(features)["home_win_prob"]
        return prob_cache[key]

    def play(home, away, neutral=False):
        known = played_playoffs.get(frozenset((home, away)))
        if known:
            return known
        return home if rng.random() < playoff_home_prob(home, away, neutral) else away

    totals = {tid: {"wins": 0.0, "playoffs": 0, "bye": 0, "conf": 0, "sb": 0} for tid in config.TEAM_IDS}

    for _ in range(n_sims):
        table = {tid: dict(rec) for tid, rec in base.items()}
        for h, a, p, margin in unplayed:
            if rng.random() < p:
                table[h]["w"] += 1; table[a]["l"] += 1
                table[h]["pd"] += margin; table[a]["pd"] -= margin
            else:
                table[a]["w"] += 1; table[h]["l"] += 1
                table[a]["pd"] += margin; table[h]["pd"] -= margin

        for tid, rec in table.items():
            g = rec["w"] + rec["l"] + rec["t"]
            rec["win_pct"] = (rec["w"] + rec["t"] * 0.5) / g if g else 0
            totals[tid]["wins"] += rec["w"] + rec["t"] * 0.5

        seeds = seeds_override or get_playoff_seeds(table, games)

        champions = {}
        for conf in config.CONFERENCES:
            s = seeds[conf]
            if len(s) < 6:
                continue
            for tid in s:
                totals[tid]["playoffs"] += 1
            totals[s[0]]["bye"] += 1
            totals[s[1]]["bye"] += 1

            wc1 = play(s[2], s[5])
            wc2 = play(s[3], s[4])
            better, worse = sorted([wc1, wc2], key=lambda t: _seed_of(t, s))
            d1 = play(s[0], worse)
            d2 = play(s[1], better)
            home, away = sorted([d1, d2], key=lambda t: _seed_of(t, s))
            champ = play(home, away)
            totals[champ]["conf"] += 1
            champions[conf] = champ

        if len(champions) == 2:
            sb_winner = play(champions["AFC"], champions["NFC"], neutral=True)
            totals[sb_winner]["sb"] += 1

    return {
        tid: {
            "expected_wins":  round(t["wins"] / n_sims, 1),
            "playoff_pct":    round(t["playoffs"] / n_sims, 3),
            "bye_pct":        round(t["bye"] / n_sims, 3),
            "conf_title_pct": round(t["conf"] / n_sims, 3),
            "sb_win_pct":     round(t["sb"] / n_sims, 3),
        }
        for tid, t in totals.items()
    }


def print_projections(projections):
    print(f"\n  {'Team':<6}{'Exp W':>7}{'Playoffs':>10}{'Bye':>7}{'Conf':>7}{'SB':>7}")
    ranked = sorted(projections.items(), key=lambda x: (-x[1]["expected_wins"], -x[1]["sb_win_pct"]))
    for tid, p in ranked:
        print(f"  {config.ABBR[tid]:<6}{p['expected_wins']:>7.1f}{p['playoff_pct']*100:>9.0f}%"
              f"{p['bye_pct']*100:>6.0f}%{p['conf_title_pct']*100:>6.0f}%{p['sb_win_pct']*100:>6.0f}%")