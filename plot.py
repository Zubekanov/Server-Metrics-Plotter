import os
import time
import requests
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE_URL = "http://zubekanov.com/api"
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def fetch_metrics(endpoint: str, params: dict = None):
	print(f"Fetching metrics from {BASE_URL}/{endpoint} with params={params}...")
	url = f"{BASE_URL}/{endpoint}"
	resp = requests.get(url, params=params)
	resp.raise_for_status()
	print(f"→ {resp.status_code} OK")
	return resp.json()


def parse_metric_data(raw: dict):
	parsed = {k: [] for k in raw}
	times = set()
	for key, items in raw.items():
		for entry in items:
			ts = datetime.fromtimestamp(entry["x"])
			parsed[key].append((ts, entry["y"]))
			times.add(ts)
	return sorted(times), parsed


def plot_single_metric(times, values, filename, ylabel, title):
	fig, ax = plt.subplots(figsize=(10, 4))

	# plot raw values with gaps for missing data
	vals_arr = np.array(values, dtype=float)
	masked_raw = np.ma.masked_invalid(vals_arr)
	ax.plot(times, masked_raw, label="Raw", alpha=0.5, linewidth=1)

	ax.set_ylabel(ylabel)
	ax.set_title(title)

	span_days = (times[-1] - times[0]).days
	if span_days < 1:
		fmt = mdates.DateFormatter("%H:%M")
	elif span_days <= 365:
		fmt = mdates.DateFormatter("%b %d")
	else:
		fmt = mdates.DateFormatter("%Y %b %d")
	ax.xaxis.set_major_formatter(fmt)
	fig.autofmt_xdate(rotation=30, ha="right")

	plt.tight_layout()
	plt.savefig(filename)
	plt.close(fig)
	print(f"Saved plot: {filename}")


def plot_timestamp_range(prefix: str, start: int = None, stop: int = None, step: int = 5):
	"""
	Fetch from /api/timestamp_metrics?start=...&stop=...&step=...
	and plot cpu_percent, ram_used, disk_used, cpu_temp without rolling averages.
	"""
	params = {}
	if start is not None:
		params["start"] = int(start)
	if stop is not None:
		params["stop"] = int(stop)
	if step is not None:
		params["step"] = int(step)

	data = fetch_metrics("timestamp_metrics", params=params)
	times, parsed = parse_metric_data(data)
	if not times:
		print(f"No data for {prefix}")
		return

	for key, label in [
		("cpu_percent", "CPU %"),
		("ram_used", "RAM Used (GiB)"),
		("disk_used", "Disk Used (GiB)"),
		("cpu_temp", "CPU Temp (°C)")
	]:
		# align values to full timeline, inserting NaN for missing
		value_map = {t: v for t, v in parsed.get(key, [])}
		aligned_vals = [value_map.get(t, float('nan')) for t in times]

		filename = os.path.join(PLOTS_DIR, f"{prefix}_{key}.png")
		title = f"{label} ({prefix.replace('_', ' ').title()})"
		plot_single_metric(times, aligned_vals, filename, label, title)

if __name__ == "__main__":
	now = int(time.time())

	# Last-hour defaults
	plot_timestamp_range("last_hour")

	# Full history, sampled hourly
	plot_timestamp_range("all", start=0, stop=now, step=3600)
