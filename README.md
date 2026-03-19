# Madden 10 Fantasy Draft Simulation

This repository contains a **Madden 10 Fantasy Draft Simulation** — a project that records every CPU vs. CPU game in a Madden 10 fantasy draft league. All game results are tracked and stored, and the project has now evolved to include an **AI-powered prediction engine** that uses historical results, team stats, and performance trends to forecast future outcomes.

We are currently in **Season 8**, with the model re-predicting after every week's results come in and logging exactly what changed.

All games are streamed live and uploaded to YouTube, and **results are updated in real time on the web app**.

---

## Links

- **YouTube Channel (Live and Archived Games):** [SimSportsStooge](https://www.youtube.com/@simsportsstooge/streams)
- **Web App:** [The Sim League](https://thesimleague.web.app/)

---

## Prediction Model

A modular Python pipeline for forecasting franchise simulation results. It ingests raw game result exports and per-team stat sheets, engineers matchup features from historical performance, and outputs win probabilities, full season projections, and playoff bracket predictions.

Every time the model runs — whether triggered by new weekly results or updated team stats — it diffs the new predictions against the previous run and surfaces exactly which games flipped winners or shifted significantly. All runs are logged with timestamps, triggers, and change summaries.

### What the model accounts for

- **Team stats** — offensive and defensive season stats including PPG, points allowed, yards per game, turnover differential, red zone TD%, and third down conversion rate, imported per team per season
- **Head-to-head history** — past matchups between two teams, weighted by recency so older seasons matter less
- **Home/away splits** — some teams perform significantly better or worse away from home
- **Road performance** — tracks teams that consistently over or underperform on the road
- **Playoff clutch factor** — measures whether a team historically outperforms or underperforms their regular season rating in the postseason
- **Rolling performance** — recent form weighted more heavily than season-long averages

### Playoff format

Built specifically for Madden 10's playoff structure — 6 teams per conference, top 2 seeds receive first-round byes, with seeds 3v6 and 4v5 in the wildcard round.

---

## Project Structure
```
madden-predict/
├── data/
│   ├── raw/                  # game result exports + per-team stat JSONs
│   └── processed/            # built feature dataset + prediction logs
├── src/
│   ├── data/                 # loaders + validators
│   ├── features/             # rolling stats, splits, h2h, playoff, ratings
│   ├── model/                # win probability + evaluation
│   ├── simulation/           # full season, standings, bracket
│   ├── tracking/             # prediction logger + diff engine
│   └── pipeline.py           # end-to-end orchestration
├── main.py                   # CLI entry point
└── config.py                 # weights, decay rates, format constants
```

---

## Tech Stack

- **Simulation:** Madden 10 (PS3/Xbox 360), CPU vs. CPU
- **Prediction model:** Python — modular feature engineering pipeline
- **Web app:** Firebase hosted React app
- **Streaming:** OBS → YouTube Live

---

## Season History

| Season | Years | Champion | Runner-Up | SB Score | Season MVP | Season Stats |
|--------|-------|----------|-----------|----------|-----|-------|
| 1 | 09-10 | St. Louis Rams | Denver Broncos | 16–9 | Kurt Warner (Eagles) | 5,973 Yds · 47 TD · 32 INT · 94.4 QBR |
| 2 | 10-11 | New York Giants | Buffalo Bills | 25–24 | Eli Manning (Giants) ⭐ | 5,141 Yds · 37 TD · 21 INT · 107.0 QBR |
| 3 | 11-12 | Denver Broncos | Tampa Bay Buccaneers | 51–10 | Matt Ryan (Ravens) | 4,907 Yds · 35 TD · 14 INT · 106.1 QBR |
| 4 | 12-13 | Cleveland Browns | Arizona Cardinals | 40–13 | Marc Bulger (Chiefs) | 5,215 Yds · 36 TD · 21 INT · 102.3 QBR |
| 5 | 13-14 | Green Bay Packers | San Diego Chargers | 40–13 | Mark Sanchez (Packers) ⭐ | 4,743 Yds · 37 TD · 19 INT · 97.5 QBR |
| 6 | 14-15 | Baltimore Ravens | Tampa Bay Buccaneers | 17–16 | Adrian Peterson (Cowboys) | 2,001 Rush Yds · 18 TD · 50 Rec · 619 Rec Yds · 4 TD |
| 7 | 15-16 | Chicago Bears | Baltimore Ravens | 38–35 | Mark Sanchez (Saints) | 5,566 Yds · 41 TD · 17 INT · 110.9 QBR |
| 8 | 16-17 | — | — | — | — | — |

*⭐ = MVP won Super Bowl that season*
