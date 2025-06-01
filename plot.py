import os
import time
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE_URL = "http://zubekanov.com/api"
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)
ROLLING_POINTS = 12

def fetch_metrics(endpoint):
	url = f"{BASE_URL}/{endpoint}"
	resp = requests.get(url)
	resp.raise_for_status()
	return resp.json()

def parse_metric_data(raw):
	parsed = {k: [] for k in raw}
	times = set()
	for key, items in raw.items():
		for entry in items:
			ts = datetime.fromtimestamp(entry["x"])
			parsed[key].append((ts, entry["y"]))
			times.add(ts)
	return sorted(times), parsed

def compute_rolling(times, values, points):
	roll_times = []
	roll_vals = []
	for i in range(len(times)):
		start = max(0, i - points + 1)
		window_vals = values[start:i+1]
		roll_times.append(times[i])
		roll_vals.append(sum(window_vals) / len(window_vals))
	return roll_times, roll_vals

def plot_single_metric(times, values, roll_times, roll_vals, filename, ylabel, title):
	fig, ax = plt.subplots(figsize=(10, 4))
	ax.plot(times, values, label="Raw", alpha=0.5, linewidth=1)
	if roll_times and roll_vals:
		ax.plot(roll_times, roll_vals, linestyle="--", label="Rolling Avg")
		ax.legend()
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

def plot_range(endpoint, prefix):
	data = fetch_metrics(endpoint)
	times, parsed = parse_metric_data(data)

	if not times:
		print(f"No data for {prefix}.")
		return

	now_ts = time.time()
	span = now_ts - times[0].timestamp()

	roll_points = ROLLING_POINTS
	if span <= 3600:
		roll_points = 12    # 1-min rolling
	elif span <= 86400:
		roll_points = 60    # 5-min rolling
	else:
		roll_points = 360   # 30-min rolling

	for key, label in [
		("cpu_percent", "CPU %"),
		("ram_used", "RAM Used (GiB)"),
		("disk_used", "Disk Used (GiB)"),
		("cpu_temp", "CPU Temp (°C)")
	]:
		entries = parsed[key]
		vals = [v for _, v in entries]
		ts   = [t for t, _ in entries]
		roll_t, roll_v = compute_rolling(ts, vals, roll_points)
		filename = os.path.join(PLOTS_DIR, f"{prefix}_{key}.png")
		title = f"{label} ({prefix.replace('_', ' ').title()})"
		plot_single_metric(ts, vals, roll_t, roll_v, filename, label, title)

if __name__ == "__main__":
	plot_range("hour_metrics", "last_hour")
	plot_range("compressed_metrics", "all_data")
