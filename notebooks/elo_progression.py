import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.data.loader import load_games
from src.features.elo import compute_elo_ratings
import config
import matplotlib.pyplot as plt
import numpy as np


def get_final_elo_for_season(season_id, elo_history):
    season_snapshots = [s for s in elo_history if s["season"] == season_id]
    if not season_snapshots:
        return {}
    last_snapshot = season_snapshots[-1]
    return last_snapshot["ratings"]


def plot_season_bar(season_id, elo_history):
    final_elos = get_final_elo_for_season(season_id, elo_history)
    if not final_elos:
        print(f"No data for season {season_id}")
        return

    sorted_teams = sorted(final_elos.items(), key=lambda x: -x[1])
    labels = [config.ABBR[t[0]] for t in sorted_teams]
    values = [t[1] for t in sorted_teams]
    colors = ["#2ecc71" if v >= 1500 else "#e74c3c" for v in values]

    plt.figure(figsize=(16, 7))
    bars = plt.bar(labels, values, color=colors, edgecolor="white", linewidth=0.5)
    plt.axhline(y=1500, color="gray", linestyle="--", alpha=0.5, label="Baseline (1500)")
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                 str(round(val, 1)), ha="center", va="bottom", fontsize=6.5, rotation=90)
    plt.title(f"Final Elo Ratings — End of Season {season_id}", fontsize=14, fontweight="bold")
    plt.ylabel("Elo Rating")
    plt.ylim(min(values) - 30, max(values) + 60)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.grid(axis="y", alpha=0.3)
    plt.show()


def plot_all_seasons_bar(elo_history):
    seasons = sorted(set(s["season"] for s in elo_history))
    teams = config.TEAM_IDS
    abbrs = [config.ABBR[t] for t in teams]

    season_elos = {}
    for season_id in seasons:
        final = get_final_elo_for_season(season_id, elo_history)
        season_elos[season_id] = [final.get(t, 1500) for t in teams]

    x = np.arange(len(teams))
    width = 0.12
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22"]

    plt.figure(figsize=(20, 8))
    for i, season_id in enumerate(seasons):
        offset = (i - len(seasons) / 2) * width
        plt.bar(x + offset, season_elos[season_id], width, label=f"S{season_id}",
                color=colors[i % len(colors)], edgecolor="white", linewidth=0.3)

    plt.axhline(y=1500, color="gray", linestyle="--", alpha=0.4, label="Baseline")
    plt.title("Elo Ratings by Team — All Seasons", fontsize=14, fontweight="bold")
    plt.ylabel("Elo Rating")
    plt.xticks(x, abbrs, rotation=45, ha="right", fontsize=8)
    plt.legend(title="Season", fontsize=8)
    plt.tight_layout()
    plt.grid(axis="y", alpha=0.3)
    plt.show()


def plot_heatmap(elo_history):
    seasons = sorted(set(s["season"] for s in elo_history))
    teams = config.TEAM_IDS

    matrix = []
    for team_id in teams:
        row = []
        for season_id in seasons:
            season_snapshots = [s for s in elo_history if s["season"] == season_id]
            if season_snapshots:
                last = season_snapshots[-1]
                row.append(last["ratings"].get(team_id, 1500))
            else:
                row.append(1500)
        matrix.append(row)

    matrix = np.array(matrix)

    avg_elos = matrix.mean(axis=1)
    sorted_indices = np.argsort(-avg_elos)
    matrix = matrix[sorted_indices]
    sorted_teams = [config.ABBR[teams[i]] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(12, 14))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=1400, vmax=1680)

    ax.set_xticks(range(len(seasons)))
    ax.set_xticklabels([f"S{s}" for s in seasons], fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(sorted_teams)))
    ax.set_yticklabels(sorted_teams, fontsize=10)

    for i in range(len(sorted_teams)):
        for j in range(len(seasons)):
            val = matrix[i, j]
            text_color = "black" if 1450 < val < 1600 else "white"
            ax.text(j, i, str(round(val, 0))[:-2],
                    ha="center", va="center", fontsize=8,
                    color=text_color, fontweight="bold")

    plt.colorbar(im, ax=ax, label="Elo Rating", shrink=0.5)
    ax.set_title("Team Elo Ratings by Season\nMadden 10 Fantasy Draft Simulation",
                 fontsize=14, fontweight="bold", pad=15)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    plt.tight_layout()
    plt.show()


def print_elo_stats(elo_history):
    teams = config.TEAM_IDS

    peak_elos = {t: {"elo": 0, "season": None, "week": None} for t in teams}
    lowest_elos = {t: {"elo": 9999, "season": None, "week": None} for t in teams}
    total_elos = {t: 0 for t in teams}
    snapshot_counts = {t: 0 for t in teams}

    for snapshot in elo_history:
        for team_id in teams:
            if team_id in snapshot["ratings"]:
                elo = snapshot["ratings"][team_id]
                total_elos[team_id] += elo
                snapshot_counts[team_id] += 1
                if elo > peak_elos[team_id]["elo"]:
                    peak_elos[team_id] = {"elo": elo, "season": snapshot["season"], "week": snapshot["week"]}
                if elo < lowest_elos[team_id]["elo"]:
                    lowest_elos[team_id] = {"elo": elo, "season": snapshot["season"], "week": snapshot["week"]}

    print("\n=== PEAK ELOS PER TEAM (highest ever achieved) ===")
    for team_id, data in sorted(peak_elos.items(), key=lambda x: -x[1]["elo"]):
        print(f"{config.ABBR[team_id]:<5} {round(data['elo'], 1):<10} S{data['season']} W{data['week']}")

    print("\n=== LOWEST ELOS PER TEAM (lowest ever achieved) ===")
    for team_id, data in sorted(lowest_elos.items(), key=lambda x: x[1]["elo"]):
        print(f"{config.ABBR[team_id]:<5} {round(data['elo'], 1):<10} S{data['season']} W{data['week']}")

    print("\n=== COMBINED ELO TOTALS (sum across all snapshots) ===")
    for team_id, total in sorted(total_elos.items(), key=lambda x: -x[1]):
        avg = total / snapshot_counts[team_id] if snapshot_counts[team_id] > 0 else 0
        print(f"{config.ABBR[team_id]:<5} Total: {round(total):<10} Avg: {round(avg, 1)}")

    print("\n=== TOP 10 PEAK ELOS EVER ===")
    seen_peaks = {}
    for snapshot in elo_history:
        for team_id, elo in snapshot["ratings"].items():
            if team_id not in seen_peaks or elo > seen_peaks[team_id]["elo"]:
                seen_peaks[team_id] = {"team": team_id, "elo": elo, "season": snapshot["season"], "week": snapshot["week"]}
    for entry in sorted(seen_peaks.values(), key=lambda x: -x["elo"])[:10]:
        print(f"{config.ABBR[entry['team']]:<5} {round(entry['elo'], 1):<10} S{entry['season']} W{entry['week']}")

    print("\n=== TOP 10 LOWEST ELOS EVER ===")
    seen_lows = {}
    for snapshot in elo_history:
        for team_id, elo in snapshot["ratings"].items():
            if team_id not in seen_lows or elo < seen_lows[team_id]["elo"]:
                seen_lows[team_id] = {"team": team_id, "elo": elo, "season": snapshot["season"], "week": snapshot["week"]}
    for entry in sorted(seen_lows.values(), key=lambda x: x["elo"])[:10]:
        print(f"{config.ABBR[entry['team']]:<5} {round(entry['elo'], 1):<10} S{entry['season']} W{entry['week']}")


if __name__ == "__main__":
    games = load_games()
    ratings, history = compute_elo_ratings(games)

    season_input = input("Enter season (1-7, ALL, or HEATMAP): ").strip().upper()

    if season_input == "ALL":
        plot_all_seasons_bar(history)
    elif season_input == "HEATMAP":
        plot_heatmap(history)
    elif season_input.isdigit() and 1 <= int(season_input) <= 7:
        plot_season_bar(int(season_input), history)
    else:
        print("Invalid input — enter a number between 1 and 7, ALL, or HEATMAP")

    print_elo_stats(history)