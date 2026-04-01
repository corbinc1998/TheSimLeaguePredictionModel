"""
update_stats.py
------------------
Reads Season 7 data from the Sim Stats xlsx and updates each team's
JSON report in the team_stats folder.

Usage:
    python update_stats.py

Edit the two paths at the top of this file before running.
"""

import json
import os
import pandas as pd

# ─── CONFIGURE THESE TWO PATHS ───────────────────────────────────────────────
XLSX_PATH = "/Users/corbin/Developer/TheSimLeaguePredictionModel/data/raw/team_stats/Sim_Stats.xlsx"
TEAM_STATS_DIR = "/Users/corbin/Developer/TheSimLeaguePredictionModel/data/raw/team_stats"
# ─────────────────────────────────────────────────────────────────────────────

# Maps uppercase team name → JSON filename stem (without _report.json)
TEAM_FILE_MAP = {
    "49ERS":       "49ers",
    "BEARS":       "bears",
    "BENGALS":     "bengals",
    "BILLS":       "bills",
    "BRONCOS":     "broncos",
    "BROWNS":      "browns",
    "BUCCANEERS":  "buccaneers",
    "CARDINALS":   "cardinals",
    "CHARGERS":    "chargers",
    "CHIEFS":      "chiefs",
    "COLTS":       "colts",
    "COMMANDERS":  "commanders",   
    "COWBOYS":     "cowboys",
    "DOLPHINS":    "dolphins",
    "EAGLES":      "eagles",
    "FALCONS":     "falcons",
    "GIANTS":      "giants",
    "JAGUARS":     "jaguars",
    "JETS":        "jets",
    "LIONS":       "lions",
    "PACKERS":     "packers",
    "PANTHERS":    "panthers",
    "PATRIOTS":    "patriots",
    "RAIDERS":     "raiders",
    "RAMS":        "rams",
    "RAVENS":      "ravens",
    "SAINTS":      "saints",
    "SEAHAWKS":    "seahawks",
    "STEELERS":    "steelers",
    "TEXANS":      "texans",
    "TITANS":      "titans",
    "VIKINGS":     "vikings",
}


def norm(name):
    if name is None:
        return None
    return str(name).upper().strip()


def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0


def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0


def rank_teams(teams, key_fn, ascending=False):
    """Returns {team: rank} where rank 1 = best."""
    vals = [(t, key_fn(t)) for t in teams if key_fn(t) is not None]
    vals.sort(key=lambda x: x[1], reverse=not ascending)
    return {t: i + 1 for i, (t, _) in enumerate(vals)}


def get(d, team, key, default=0):
    return d.get(team, {}).get(key, default)


# ─── Load xlsx ────────────────────────────────────────────────────────────────
print(f"Reading {XLSX_PATH}...")
sheets = pd.read_excel(XLSX_PATH, sheet_name=None, header=0)

# ─── Parse S7 sheets ──────────────────────────────────────────────────────────
off_rows, def_rows, conv_rows, rz_rows, pen_rows, to_rows = {}, {}, {}, {}, {}, {}

for _, r in sheets["S7 Offense"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    off_rows[t] = dict(
        total_yards=safe_float(r.iloc[2]),   # Total Offense (pass+rush)
        pass_yards=safe_float(r.iloc[3]),
        rush_yards=safe_float(r.iloc[4]),
        ppg=safe_float(r.iloc[5]),
        pass_tds=safe_int(r.iloc[6]),
        rush_tds=safe_int(r.iloc[7]),
        first_downs=safe_int(r.iloc[9]),
    )

for _, r in sheets["S7 Defense"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    def_rows[t] = dict(
        yards_allowed=safe_float(r.iloc[1]),
        pass_yards_allowed=safe_float(r.iloc[2]),
        rush_yards_allowed=safe_float(r.iloc[3]),
        points_allowed=safe_float(r.iloc[4]),
        sacks=safe_int(r.iloc[5]),
        fumbles_forced=safe_int(r.iloc[6]),
        interceptions=safe_int(r.iloc[7]),
    )

for _, r in sheets["S7 Conversions"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    conv_rows[t] = dict(
        third_down_pct=safe_float(r.iloc[3]),
        fourth_down_pct=safe_float(r.iloc[6]),
    )

for _, r in sheets["S7 RedZone"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    att = safe_float(r.iloc[1])
    td  = safe_float(r.iloc[2])
    rz_rows[t] = dict(
        redzone_att=int(att),
        redzone_tds=int(td),
        redzone_td_pct=round(td / att, 4) if att else 0,
    )

for _, r in sheets["S7 Penalties"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    pen_rows[t] = dict(
        penalties=safe_int(r.iloc[1]),
        penalty_yards=safe_int(r.iloc[2]),
    )

for _, r in sheets["S7 Turnovers"].iterrows():
    t = norm(r.iloc[0])
    if not t or t in ("TEAM", "NAN", "NONE"):
        continue
    to_rows[t] = dict(
        differential=safe_int(r.iloc[1]),
        given=safe_int(r.iloc[2]),
        taken=safe_int(r.iloc[5]),
        int_thrown=safe_int(r.iloc[3]),
        int_caught=safe_int(r.iloc[6]),
        fumbles_lost=safe_int(r.iloc[4]),
        fumbles_recovered=safe_int(r.iloc[7]),
    )

all_teams = sorted(
    set(off_rows) | set(def_rows) | set(conv_rows) | set(rz_rows) | set(pen_rows) | set(to_rows)
)
print(f"Found {len(all_teams)} teams in S7 data")

# ─── Compute rankings ─────────────────────────────────────────────────────────
ranks = {
    # Offense — higher = better
    "total_yards":      rank_teams(all_teams, lambda t: get(off_rows, t, "total_yards"),    ascending=False),
    "pass_yards":       rank_teams(all_teams, lambda t: get(off_rows, t, "pass_yards"),      ascending=False),
    "rush_yards":       rank_teams(all_teams, lambda t: get(off_rows, t, "rush_yards"),      ascending=False),
    "ppg":              rank_teams(all_teams, lambda t: get(off_rows, t, "ppg"),             ascending=False),
    "total_tds":        rank_teams(all_teams, lambda t: get(off_rows, t, "pass_tds") + get(off_rows, t, "rush_tds"), ascending=False),
    "first_downs":      rank_teams(all_teams, lambda t: get(off_rows, t, "first_downs"),     ascending=False),
    # Defense — lower yards/points = better
    "yards_allowed":    rank_teams(all_teams, lambda t: get(def_rows, t, "yards_allowed"),   ascending=True),
    "pass_yds_allowed": rank_teams(all_teams, lambda t: get(def_rows, t, "pass_yards_allowed"), ascending=True),
    "rush_yds_allowed": rank_teams(all_teams, lambda t: get(def_rows, t, "rush_yards_allowed"), ascending=True),
    "pts_allowed":      rank_teams(all_teams, lambda t: get(def_rows, t, "points_allowed"),  ascending=True),
    "def_sacks":        rank_teams(all_teams, lambda t: get(def_rows, t, "sacks"),           ascending=False),
    "def_ints":         rank_teams(all_teams, lambda t: get(def_rows, t, "interceptions"),   ascending=False),
    # Efficiency — higher = better
    "third_down":       rank_teams(all_teams, lambda t: get(conv_rows, t, "third_down_pct"), ascending=False),
    "fourth_down":      rank_teams(all_teams, lambda t: get(conv_rows, t, "fourth_down_pct"), ascending=False),
    "rz_td_pct":        rank_teams(all_teams, lambda t: get(rz_rows, t, "redzone_td_pct"),  ascending=False),
    "to_diff":          rank_teams(all_teams, lambda t: get(to_rows, t, "differential"),     ascending=False),
    # Discipline — lower = better
    "penalties":        rank_teams(all_teams, lambda t: get(pen_rows, t, "penalties"),       ascending=True),
    "pen_yards":        rank_teams(all_teams, lambda t: get(pen_rows, t, "penalty_yards"),   ascending=True),
    # Turnovers given: least given (closest to 0) = best = rank 1
    "to_given":         rank_teams(all_teams, lambda t: get(to_rows, t, "given"),            ascending=False),
}


def build_s7_block(t):
    o  = off_rows.get(t, {})
    d  = def_rows.get(t, {})
    c  = conv_rows.get(t, {})
    rz = rz_rows.get(t, {})
    p  = pen_rows.get(t, {})
    tv = to_rows.get(t, {})
    total_tds = o.get("pass_tds", 0) + o.get("rush_tds", 0)

    return {
        "offense": {
            "total_yards": o.get("total_yards", 0),
            "pass_yards":  o.get("pass_yards",  0),
            "rush_yards":  o.get("rush_yards",  0),
            "ppg":         o.get("ppg",         0),
            "pass_tds":    o.get("pass_tds",    0),
            "rush_tds":    o.get("rush_tds",    0),
            "first_downs": o.get("first_downs", 0),
        },
        "defense": {
            "yards_allowed":      d.get("yards_allowed",      0),
            "pass_yards_allowed": d.get("pass_yards_allowed", 0),
            "rush_yards_allowed": d.get("rush_yards_allowed", 0),
            "points_allowed":     d.get("points_allowed",     0),
            "sacks":              d.get("sacks",              0),
            "interceptions":      d.get("interceptions",      0),
            "fumbles_forced":     d.get("fumbles_forced",     0),
        },
        "efficiency": {
            "third_down_pct":  c.get("third_down_pct",  0),
            "fourth_down_pct": c.get("fourth_down_pct", 0),
            "redzone_att":     rz.get("redzone_att",    0),
            "redzone_tds":     rz.get("redzone_tds",    0),
            "redzone_td_pct":  rz.get("redzone_td_pct", 0),
        },
        "turnovers": {
            "differential":      tv.get("differential",      0),
            "given":             tv.get("given",             0),
            "taken":             tv.get("taken",             0),
            "int_thrown":        tv.get("int_thrown",        0),
            "int_caught":        tv.get("int_caught",        0),
            "fumbles_lost":      tv.get("fumbles_lost",      0),
            "fumbles_recovered": tv.get("fumbles_recovered", 0),
        },
        "discipline": {
            "penalties":     p.get("penalties",     0),
            "penalty_yards": p.get("penalty_yards", 0),
        },
    }


def build_s7_rankings(t):
    o  = off_rows.get(t, {})
    d  = def_rows.get(t, {})
    c  = conv_rows.get(t, {})
    rz = rz_rows.get(t, {})
    p  = pen_rows.get(t, {})
    tv = to_rows.get(t, {})
    total_tds = o.get("pass_tds", 0) + o.get("rush_tds", 0)

    return {
        "offense": {
            "total_yards":  {"rank": ranks["total_yards"].get(t),  "value": o.get("total_yards",  0)},
            "pass_yards":   {"rank": ranks["pass_yards"].get(t),   "value": o.get("pass_yards",   0)},
            "rush_yards":   {"rank": ranks["rush_yards"].get(t),   "value": o.get("rush_yards",   0)},
            "ppg":          {"rank": ranks["ppg"].get(t),          "value": o.get("ppg",          0)},
            "total_tds":    {"rank": ranks["total_tds"].get(t),    "value": total_tds},
            "first_downs":  {"rank": ranks["first_downs"].get(t),  "value": o.get("first_downs",  0)},
        },
        "defense": {
            "yards_allowed":      {"rank": ranks["yards_allowed"].get(t),    "value": d.get("yards_allowed",      0)},
            "pass_yards_allowed": {"rank": ranks["pass_yds_allowed"].get(t), "value": d.get("pass_yards_allowed", 0)},
            "rush_yards_allowed": {"rank": ranks["rush_yds_allowed"].get(t), "value": d.get("rush_yards_allowed", 0)},
            "points_allowed":     {"rank": ranks["pts_allowed"].get(t),      "value": d.get("points_allowed",     0)},
            "sacks":              {"rank": ranks["def_sacks"].get(t),        "value": d.get("sacks",              0)},
            "interceptions":      {"rank": ranks["def_ints"].get(t),         "value": d.get("interceptions",      0)},
        },
        "efficiency": {
            "third_down_pct":  {"rank": ranks["third_down"].get(t),  "value": c.get("third_down_pct",  0)},
            "fourth_down_pct": {"rank": ranks["fourth_down"].get(t), "value": c.get("fourth_down_pct", 0)},
            "redzone_td_pct":  {"rank": ranks["rz_td_pct"].get(t),   "value": rz.get("redzone_td_pct", 0)},
            "turnover_diff":   {"rank": ranks["to_diff"].get(t),     "value": tv.get("differential",   0)},
        },
        "discipline": {
            "penalties":       {"rank": ranks["penalties"].get(t), "value": p.get("penalties",     0)},
            "penalty_yards":   {"rank": ranks["pen_yards"].get(t), "value": p.get("penalty_yards", 0)},
            "turnovers_given": {"rank": ranks["to_given"].get(t),  "value": tv.get("given",        0)},
        },
    }


# ─── Update each team JSON ────────────────────────────────────────────────────
updated, skipped = 0, 0

for team_name in all_teams:
    file_stem = TEAM_FILE_MAP.get(team_name)
    if not file_stem:
        print(f"  ⚠  No file mapping for {team_name}, skipping")
        skipped += 1
        continue

    json_path = os.path.join(TEAM_STATS_DIR, f"{file_stem}_report.json")
    if not os.path.exists(json_path):
        print(f"  ⚠  File not found: {json_path}, skipping")
        skipped += 1
        continue

    with open(json_path) as f:
        report = json.load(f)

    # Add S7 season data
    report.setdefault("season_by_season", {})["7"] = build_s7_block(team_name)

    # Add S7 rankings
    report.setdefault("rankings", {}).setdefault("by_season", {})["7"] = build_s7_rankings(team_name)

    # Update seasons_analyzed if present
    if "seasons_analyzed" in report and 7 not in report["seasons_analyzed"]:
        report["seasons_analyzed"].append(7)

    # Update aggregated_stats
    sbs = report["season_by_season"]
    seasons_played = len(sbs)
    seasons_with_data = [str(s) for s in range(1, seasons_played + 1) if str(s) in sbs]

    agg = report.setdefault("aggregated_stats", {})
    agg["seasons_played"] = seasons_played
    agg["total_offensive_yards"] = round(sum(sbs[s]["offense"]["total_yards"] for s in seasons_with_data if "offense" in sbs[s]), 1)
    agg["total_points_scored"]   = round(sum(sbs[s]["offense"]["ppg"] * 16    for s in seasons_with_data if "offense" in sbs[s]), 1)
    agg["total_points_allowed"]  = round(sum(sbs[s]["defense"]["points_allowed"] for s in seasons_with_data if "defense" in sbs[s]), 1)
    agg["total_turnovers_forced"]= sum(sbs[s]["turnovers"]["taken"]            for s in seasons_with_data if "turnovers" in sbs[s])
    agg["total_turnovers_given"] = sum(abs(sbs[s]["turnovers"]["given"])       for s in seasons_with_data if "turnovers" in sbs[s])
    agg["avg_ppg"]               = round(sum(sbs[s]["offense"]["ppg"]          for s in seasons_with_data if "offense" in sbs[s]) / seasons_played, 4)
    agg["avg_points_allowed"]    = round(agg["total_points_allowed"] / seasons_played, 4)
    agg["avg_turnover_diff"]     = round(sum(sbs[s]["turnovers"]["differential"] for s in seasons_with_data if "turnovers" in sbs[s]) / seasons_played, 4)

    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"  ✓  {json_path}")
    updated += 1

print(f"\nDone — {updated} updated, {skipped} skipped")

# ─── Rebuild master_summary.json and TEAM_RANKINGS_SUMMARY.txt ───────────────
print("\nRebuilding summary files...")

GAMES = 16
team_seasons = {}

for s in range(1, 8):
    off_sheet = sheets.get(f"S{s} Offense")
    def_sheet = sheets.get(f"S{s} Defense")
    to_sheet  = sheets.get(f"S{s} Turnovers")
    if off_sheet is None:
        continue
    for _, r in off_sheet.iterrows():
        t = norm(r.iloc[0])
        if not t or t in ("TEAM", "NAN", "NONE"):
            continue
        team_seasons.setdefault(t, {})[s] = {
            "ppg":       safe_float(r.iloc[5]),
            "off_yards": safe_float(r.iloc[2]),
        }
    if def_sheet is not None:
        for _, r in def_sheet.iterrows():
            t = norm(r.iloc[0])
            if not t or t in ("TEAM", "NAN", "NONE"):
                continue
            if t in team_seasons and s in team_seasons[t]:
                team_seasons[t][s]["pts_allowed"] = safe_float(r.iloc[4])
    if to_sheet is not None:
        for _, r in to_sheet.iterrows():
            t = norm(r.iloc[0])
            if not t or t in ("TEAM", "NAN", "NONE"):
                continue
            if t in team_seasons and s in team_seasons[t]:
                team_seasons[t][s]["to_diff"] = safe_int(r.iloc[1])

summary_teams = sorted(team_seasons.keys())

def team_agg(team):
    seasons = team_seasons[team]
    ppgs        = [v["ppg"]         for v in seasons.values() if "ppg"         in v]
    pts_allowed = [v["pts_allowed"] for v in seasons.values() if "pts_allowed" in v]
    to_diffs    = [v["to_diff"]     for v in seasons.values() if "to_diff"     in v]
    off_yards   = [v["off_yards"]   for v in seasons.values() if "off_yards"   in v]
    n = len(seasons)
    avg_ppg = sum(ppgs) / len(ppgs)               if ppgs        else 0
    avg_pa  = sum(pts_allowed) / len(pts_allowed) if pts_allowed else 0
    avg_to  = sum(to_diffs) / len(to_diffs)       if to_diffs    else 0
    pt_diff = sum(p * GAMES for p in ppgs) - sum(pts_allowed)
    return dict(
        seasons_played        = n,
        avg_ppg               = round(avg_ppg, 1),
        avg_points_allowed    = round(avg_pa,  1),
        avg_turnover_diff     = round(avg_to,  1),
        total_offensive_yards = int(sum(off_yards)),
        point_differential    = int(round(pt_diff)),
    )

summaries = {t: team_agg(t) for t in summary_teams}

def rank_overall(key, ascending=False):
    return sorted(summary_teams, key=lambda t: summaries[t][key], reverse=not ascending)

overall_off    = rank_overall("avg_ppg",            ascending=False)
overall_def    = rank_overall("avg_points_allowed", ascending=True)
overall_to     = rank_overall("avg_turnover_diff",  ascending=False)
overall_ptdiff = rank_overall("point_differential", ascending=False)

off_rank = {t: i+1 for i,t in enumerate(overall_off)}
def_rank = {t: i+1 for i,t in enumerate(overall_def)}
to_rank  = {t: i+1 for i,t in enumerate(overall_to)}

# ── master_summary.json ───────────────────────────────────────────────────────
master = {
    "seasons_analyzed": list(range(1, 8)),
    "total_teams": len(summary_teams),
    "overall_rankings": {
        "overall_offense":       overall_off,
        "overall_defense":       overall_def,
        "overall_turnover_diff": overall_to,
        "overall_point_diff":    overall_ptdiff,
    },
    "team_summaries": {
        t: {
            "seasons_played":         summaries[t]["seasons_played"],
            "avg_ppg":                summaries[t]["avg_ppg"],
            "avg_points_allowed":     summaries[t]["avg_points_allowed"],
            "avg_turnover_diff":      summaries[t]["avg_turnover_diff"],
            "total_offensive_yards":  summaries[t]["total_offensive_yards"],
            "overall_offense_rank":   off_rank[t],
            "overall_defense_rank":   def_rank[t],
            "overall_turnover_rank":  to_rank[t],
        }
        for t in summary_teams
    },
}

master_path = os.path.join(TEAM_STATS_DIR, "master_summary.json")
with open(master_path, "w") as f:
    json.dump(master, f, indent=2)
print(f"  ✓  {master_path}")

# ── TEAM_RANKINGS_SUMMARY.txt ─────────────────────────────────────────────────
W = 80
lines = [
    "=" * W,
    "NFL TEAM STATISTICAL RANKINGS - SEASONS 1-7",
    "=" * W,
    "",
    "Seasons Analyzed: 1, 2, 3, 4, 5, 6, 7",
    f"Total Teams: {len(summary_teams)}",
    "",
]

def add_section(title, ranked, fmt_fn):
    lines.append("-" * W)
    lines.append(title)
    lines.append("-" * W)
    for i, t in enumerate(ranked, 1):
        lines.append(f"{i:>2}. {t:<22} {fmt_fn(t)}")
    lines.append("")

add_section(
    "OVERALL OFFENSIVE RANKINGS (Average PPG)",
    overall_off,
    lambda t: f"{summaries[t]['avg_ppg']:.1f} PPG",
)
add_section(
    "OVERALL DEFENSIVE RANKINGS (Average Points Allowed)",
    overall_def,
    lambda t: f"{summaries[t]['avg_points_allowed']:.1f} PA/Season",
)
add_section(
    "OVERALL TURNOVER DIFFERENTIAL RANKINGS",
    overall_to,
    lambda t: (f"+{summaries[t]['avg_turnover_diff']:.1f}"
               if summaries[t]["avg_turnover_diff"] >= 0
               else f"{summaries[t]['avg_turnover_diff']:.1f}") + " TO Diff/Season",
)
add_section(
    "OVERALL POINT DIFFERENTIAL RANKINGS",
    overall_ptdiff,
    lambda t: (f"+{summaries[t]['point_differential']}"
               if summaries[t]["point_differential"] >= 0
               else str(summaries[t]["point_differential"]))
              + f" Point Diff ({summaries[t]['seasons_played']} seasons)",
)

txt_path = os.path.join(TEAM_STATS_DIR, "TEAM_RANKINGS_SUMMARY.txt")
with open(txt_path, "w") as f:
    f.write("\n".join(lines))
print(f"  ✓  {txt_path}")
print("\nAll done!")