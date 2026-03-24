import os

TEAMS = {
    # AFC North
    "pit": {"name": "Steelers",  "conference": "AFC", "division": "North"},
    "bal": {"name": "Ravens",    "conference": "AFC", "division": "North"},
    "cle": {"name": "Browns",    "conference": "AFC", "division": "North"},
    "cin": {"name": "Bengals",   "conference": "AFC", "division": "North"},
    # AFC East
    "buf": {"name": "Bills",     "conference": "AFC", "division": "East"},
    "ne":  {"name": "Patriots",  "conference": "AFC", "division": "East"},
    "mia": {"name": "Dolphins",  "conference": "AFC", "division": "East"},
    "nyj": {"name": "Jets",      "conference": "AFC", "division": "East"},
    # AFC South
    "ten": {"name": "Titans",    "conference": "AFC", "division": "South"},
    "hou": {"name": "Texans",    "conference": "AFC", "division": "South"},
    "ind": {"name": "Colts",     "conference": "AFC", "division": "South"},
    "jax": {"name": "Jaguars",   "conference": "AFC", "division": "South"},
    # AFC West
    "kc":  {"name": "Chiefs",    "conference": "AFC", "division": "West"},
    "oak": {"name": "Raiders",   "conference": "AFC", "division": "West"},
    "den": {"name": "Broncos",   "conference": "AFC", "division": "West"},
    "sd":  {"name": "Chargers",  "conference": "AFC", "division": "West"},
    # NFC North
    "gb":  {"name": "Packers",   "conference": "NFC", "division": "North"},
    "chi": {"name": "Bears",     "conference": "NFC", "division": "North"},
    "det": {"name": "Lions",     "conference": "NFC", "division": "North"},
    "min": {"name": "Vikings",   "conference": "NFC", "division": "North"},
    # NFC East
    "dal": {"name": "Cowboys",   "conference": "NFC", "division": "East"},
    "nyg": {"name": "Giants",    "conference": "NFC", "division": "East"},
    "phi": {"name": "Eagles",    "conference": "NFC", "division": "East"},
    "was": {"name": "Commanders","conference": "NFC", "division": "East"},
    # NFC South
    "no":  {"name": "Saints",    "conference": "NFC", "division": "South"},
    "tb":  {"name": "Buccaneers","conference": "NFC", "division": "South"},
    "car": {"name": "Panthers",  "conference": "NFC", "division": "South"},
    "atl": {"name": "Falcons",   "conference": "NFC", "division": "South"},
    # NFC West
    "sf":  {"name": "49ers",     "conference": "NFC", "division": "West"},
    "sea": {"name": "Seahawks",  "conference": "NFC", "division": "West"},
    "ari": {"name": "Cardinals", "conference": "NFC", "division": "West"},
    "stl": {"name": "Rams",      "conference": "NFC", "division": "West"},
}


TEAM_IDS = list(TEAMS.keys())

CONFERENCES = ["AFC", "NFC"]

DIVISIONS = ["North", "East", "South", "West"]

ABBR = {
    "pit": "PIT", "bal": "BAL", "cle": "CLE", "cin": "CIN",
    "buf": "BUF", "ne":  "NE",  "mia": "MIA", "nyj": "NYJ",
    "ten": "TEN", "hou": "HOU", "ind": "IND", "jax": "JAX",
    "kc":  "KC",  "oak": "LV",  "den": "DEN", "sd":  "LAC",
    "gb":  "GB",  "chi": "CHI", "det": "DET", "min": "MIN",
    "dal": "DAL", "nyg": "NYG", "phi": "PHI", "was": "WAS",
    "no":  "NO",  "tb":  "TB",  "car": "CAR", "atl": "ATL",
    "sf":  "SF",  "sea": "SEA", "ari": "ARI", "stl": "LAR",
}

TEAM_STAT_FILES = {
    "pit": "steelers_report",
    "bal": "ravens_report",
    "cle": "browns_report",
    "cin": "bengals_report",
    "buf": "bills_report",
    "ne":  "patriots_report",
    "mia": "dolphins_report",
    "nyj": "jets_report",
    "ten": "titans_report",
    "hou": "texans_report",
    "ind": "colts_report",
    "jax": "jaguars_report",
    "kc":  "chiefs_report",
    "oak": "raiders_report",
    "den": "broncos_report",
    "sd":  "chargers_report",
    "gb":  "packers_report",
    "chi": "bears_report",
    "det": "lions_report",
    "min": "vikings_report",
    "dal": "cowboys_report",
    "nyg": "giants_report",
    "phi": "eagles_report",
    "was": "commanders_report",
    "no":  "saints_report",
    "tb":  "buccaneers_report",
    "car": "panthers_report",
    "atl": "falcons_report",
    "sf":  "49ers_report",
    "sea": "seahawks_report",
    "ari": "cardinals_report",
    "stl": "rams_report",
}

# Season constants




# Current season number
CURRENT_SEASON = 8
# Regular season week count (17)
REGULAR_SEASON_WEEKS = 17
# First season (1) — useful for loops and validation
FIRST_SEASON = 1

# Playoff format

# Teams per conference (6)
PLAYOFF_TEAMS_PER_CONF = 6

# Which seeds get byes (1, 2)

PLAYOFF_BYE_SEEDS = [1, 2]

# Wildcard matchup pairs (3v6, 4v5)
PLAYOFF_WILDCARD_MATCHUPS = [(3, 6), (4, 5)]

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Base dir, data dir, raw dir, processed dir
DATA_DIR      = os.path.join(BASE_DIR, "data")
RAW_DIR       = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# Path to games.json
GAMES_PATH      = os.path.join(RAW_DIR, "games.json")
# Path to team_stats/ folder
TEAM_STATS_DIR    = os.path.join(RAW_DIR, "team_stats")
# Path to predictions_log.json
PREDICTIONS_PATH   = os.path.join(PROCESSED_DIR, "predictions_log.json")
# Path to features.csv
FEATURES_PATH   = os.path.join(PROCESSED_DIR, "features.csv")


# Feature parameters

# Rolling window size (how many recent games to look back)
ROLLING_WINDOW = 5
# H2H decay rate
H2H_DECAY = 0.75
# Minimum H2H sample before applying an edge
MIN_SAMPLE_H2H = 2
# Minimum playoff games before applying clutch factor
MIN_SAMPLE_PLAYOFF = 3
# Minimum win streak length before applying a streak boost
MIN_STREAK_GAMES = 3
# Minimum consecutive winning seasons before applying a momentum boost
MIN_WINNING_SEASONS = 2
# Season recency decay for general stats (not just h2h)
SEASON_DECAY = 0.80
# Minimum games a team must have played before rolling stats are trusted
MIN_GAMES_PLAYED = 3
# Cap point differential per game to reduce blowout skew
MARGIN_CAP = 28
# Weight of prior season stats when current season sample is small
PRIOR_SEASON_WEIGHT = 0.6
# Minimum home/away games before trusting home/away splits
MIN_HOME_GAMES = 4
MIN_AWAY_GAMES = 4

# Model weights

# One weight per feature (home boost, road factor, h2h edge, h2h margin, playoff clutch)
WEIGHTS = {
    "home_boost":       0.6,   # how much a team's personal home record matters
    "away_factor":      0.4,   # how much the away team's road record matters
    "h2h_edge":         0.5,   # how much head-to-head history matters
    "h2h_margin":       0.15,  # how much avg point margin in h2h matters
    "playoff_clutch":   0.4,   # how much playoff over/underperformance matters
    "streak":           0.3,   # how much current win/loss streak matters
}

# Elo rating system
ELO_INITIAL = 1500        # starting Elo for every team at the beginning of the sim
ELO_K_FACTOR = 20         # how much each game shifts the rating — higher = more volatile
ELO_K_PLAYOFF = 30        # playoffs count more, so a higher K factor
ELO_HOME_ADVANTAGE = 65   # Elo points added to home team before calculating expected outcome


# Logistic scale factor
LOGISTIC_SCALE = 0.13
# Raw home field advantage added to every home team's edge regardless of which teams are playing
HOME_FIELD_ADVANTAGE = 2.8
# Rating floor and ceiling
RATING_MIN = 25
RATING_MAX = 82


# Stat baselines

# The "average" value for each stat — what a 50-rated team looks like
# PPG baseline, points allowed baseline, turnover diff baseline, etc.

STAT_BASELINES = {
    "ppg":             28.3,   # avg offensive points scored per game (excl. def/st TDs)
    "points_allowed":  26.7,   # avg total points allowed per game (incl. def/st TDs scored by opponent)
    "turnover_diff":    0.0,
    "redzone_td_pct":  50.2,
    "third_down_pct":  40.1,
}

#  The ~1.6 PPG gap represents the average defensive/special teams scoring across

# Diff thresholds

# Minimum shift to log as a change (noise floor)
# Threshold for "major" vs "minor" shift

# Minimum win probability shift to bother logging (noise floor)
# Below this — ignore it completely
DIFF_MIN_SHIFT = 0.03       # 3 percentage points

# Shift threshold that separates "major" from "minor"
# Above this — flag it prominently in the change log
DIFF_MAJOR_SHIFT = 0.08     # 8 percentage points


# So the three tiers end up being:

# 0pp  → 3pp   ignored completely — noise
# 3pp  → 8pp   logged as minor shift
# 8pp+         logged as major shift
# flip         winner changed — always flagged regardless of shift size
