# System Metrics Plotter

This Python script fetches and visualises system performance metrics from [zubekanov.com](http://zubekanov.com), my personal website.

The script queries API endpoints hosted on the site to retrieve:
- Metrics for the last hour
- Metrics for all-time trends

## Features
- Fetches metrics data via HTTP
- Generates plots with rolling averages
- Saves output charts to `plots/` in the same directory

## Usage
```bash
python plot.py
```

Install dependencies with:
```bash
pip install matplotlib requests
```
