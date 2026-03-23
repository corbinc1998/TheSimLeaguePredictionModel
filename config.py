# =============================================================================
# config.py
# =============================================================================

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