import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd


def _save_figure(fig, output_dir, stem):
    for extension in ("svg", "png", "pdf"):
        fig.savefig(output_dir / f"{stem}.{extension}", bbox_inches="tight")


def analyse(data_path, output_dir):
    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    with data_path.open("r", newline="", encoding="utf-8", errors="replace") as handle:
        rows = [row for row in csv.reader(handle) if len(row) >= 5]

    if not rows:
        return "none"

    times, levels, event_ids = {}, {"notice": 0, "error": 0, "warn": 0}, {f"E{i}": 0 for i in range(1, 7)}
    parsed_times = []
    for row in rows:
        stamp, level, event_id = row[1], row[2].lower(), row[4]
        times[stamp] = times.get(stamp, 0) + 1
        if level in levels:
            levels[level] += 1
        if event_id in event_ids:
            event_ids[event_id] += 1
        try:
            parsed_times.append(pd.to_datetime(stamp, format="%a %b %d %H:%M:%S %Y"))
        except (ValueError, TypeError):
            pass

    fig = Figure(figsize=(9, 4)); ax = fig.subplots()
    ax.plot(list(times.keys()), list(times.values())); ax.grid(True)
    if len(times) > 1:
        keys = list(times.keys()); ax.set_xticks([keys[0], keys[len(keys)//2], keys[-1]] if len(keys) > 3 else [keys[0], keys[-1]])
    ax.set_xlabel("Time"); ax.set_ylabel("Events per Second"); ax.set_title("Events per Second vs Time")
    fig.autofmt_xdate(rotation=20); _save_figure(fig, output_dir, "EperSvsT")

    fig = Figure(figsize=(6, 5)); ax = fig.subplots()
    nonzero_levels = {k: v for k, v in levels.items() if v}
    if nonzero_levels:
        ax.pie(list(nonzero_levels.values()), labels=list(nonzero_levels.keys()), autopct="%1.2f%%")
    else:
        ax.text(.5, .5, "No level data", ha="center", va="center")
    ax.set_title("Log Level Distribution"); _save_figure(fig, output_dir, "LsPiChart")

    fig = Figure(figsize=(7, 4)); ax = fig.subplots()
    ax.bar(list(event_ids.keys()), list(event_ids.values())); ax.grid(axis="y")
    ax.set_title("Frequency of Event IDs"); ax.set_xlabel("Event ID"); ax.set_ylabel("Occurrences")
    _save_figure(fig, output_dir, "Esbar")

    fig = Figure(figsize=(9, 4)); ax = fig.subplots()
    if parsed_times:
        parsed_times.sort()
        counts = {}
        for stamp in parsed_times:
            counts[stamp] = counts.get(stamp, 0) + 1
        ax.plot(list(counts.keys()), list(counts.values()))
        fig.autofmt_xdate(rotation=20)
    ax.grid(True); ax.set_xlabel("Time"); ax.set_ylabel("Events per Second"); ax.set_title("Events per Second (Time Series)")
    _save_figure(fig, output_dir, "Realtime")
    return "ok"
