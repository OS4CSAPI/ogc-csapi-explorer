"""
Run key cells from Narasimha Sharma's CSAPI LiveML Pipeline notebook.
Adapted from his Google Colab notebook for local execution.

Produces:
  - uas_track.csv, lob_data.csv, senrep_data.csv  (data collection)
  - csapi_dashboard.png                            (intelligence dashboard)
  - csapi_ml_dashboard.png                         (ML anomaly + prediction)
  - csapi_live_map.html                            (interactive Folium map)
"""

import requests, json, time, math, csv, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import folium
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════
BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = ("os4csapi", "ogc134mm")
HDR  = {"Accept": "application/json"}

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "notebook_output")
os.makedirs(OUT_DIR, exist_ok=True)

def out(name):
    return os.path.join(OUT_DIR, name)

def get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", auth=AUTH, headers=HDR,
                         params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  X Error on {path}: {e}")
        return {}

def get_latest(ds_id, limit=30):
    try:
        r = requests.get(
            f"{BASE}/datastreams/{ds_id}/observations",
            auth=AUTH, headers=HDR,
            params={"limit": limit}, timeout=15)
        return r.json().get("items", [])
    except:
        return []

# ═══════════════════════════════════════════════════════════════════
#  STEP 1: SERVER HEALTH + DISCOVERY
# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("  Narasimha Sharma's CSAPI LiveML Pipeline")
print("  (Aganitha Space — adapted for local execution)")
print("=" * 60)

data = get("/")
if not data:
    print("  X Server unreachable. Is the simulator running?")
    sys.exit(1)
print(f"  V Server: {data.get('title', 'N/A')}")

# Systems
systems = get("/systems", params={"limit": 50}).get("items", [])
print(f"  V Systems discovered: {len(systems)}")
for s in systems:
    name = s.get("properties", {}).get("name", "Unnamed")
    sid = s.get("id", "?")
    print(f"    - {name} ({sid})")

# Datastreams
ds_all = get("/datastreams", params={"limit": 100}).get("items", [])
print(f"  V Datastreams discovered: {len(ds_all)}")

# ═══════════════════════════════════════════════════════════════════
#  STEP 2: DATA COLLECTION (single snapshot — not a polling loop)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  Collecting observations...")
print("=" * 60)

# UAS Location Estimates
uas_records = []
for obs in get_latest("04f0", 50):
    r = obs.get("result", {})
    # Filter for genuine localizer fixes (not scope-leaked LOBs)
    if "estimatedLat" not in r:
        continue
    uas_records.append({
        "phenomenonTime": obs.get("phenomenonTime", ""),
        "trackId": r.get("trackId", ""),
        "estimatedLat": r.get("estimatedLat", ""),
        "estimatedLon": r.get("estimatedLon", ""),
        "cep50_m": r.get("cep50_m", ""),
        "classification": r.get("classification", ""),
        "numContributingLobs": r.get("numContributingLobs", ""),
        "contributingSensors": r.get("contributingSensors", ""),
        "residual_m": r.get("residual_m", ""),
    })
print(f"  UAS fixes collected: {len(uas_records)}")

# LOBs from all 3 sensors
lob_records = []
for ds_id, sensor_name in [("04c0", "AZ-MA-1"), ("04cg", "AZ-MA-2"), ("04d0", "AZ-MA-3")]:
    for obs in get_latest(ds_id, 30):
        r = obs.get("result", {})
        if "bearingTrue" not in r:
            continue
        lob_records.append({
            "phenomenonTime": obs.get("phenomenonTime", ""),
            "sensor": sensor_name,
            "trackId": r.get("trackId", ""),
            "bearingTrue": r.get("bearingTrue", ""),
            "bearingStdDev": r.get("bearingStdDev", ""),
            "sensorLat": r.get("sensorLat", ""),
            "sensorLon": r.get("sensorLon", ""),
            "classification": r.get("classification", ""),
        })
print(f"  LOBs collected: {len(lob_records)}")

# SENREPs
senrep_records = []
for obs in get_latest("044g", 10):
    r = obs.get("result", {})
    senrep_records.append({
        "phenomenonTime": obs.get("phenomenonTime", ""),
        "title": r.get("title", ""),
        "senderId": r.get("senderId", ""),
        "seqNo": r.get("seqNo", ""),
        "tgtTyp": r.get("tgtTyp", ""),
        "subTyp": r.get("subTyp", ""),
        "etaLat": r.get("etaLat", ""),
        "etaLon": r.get("etaLon", ""),
        "etaTimeZ": r.get("etaTimeZ", ""),
        "detectTimeZ": r.get("detectTimeZ", ""),
        "comments": r.get("comments", ""),
    })
print(f"  SENREPs collected: {len(senrep_records)}")

# Save CSVs
uas_df = pd.DataFrame(uas_records)
lob_df = pd.DataFrame(lob_records)
sen_df = pd.DataFrame(senrep_records)

uas_df.to_csv(out("uas_track.csv"), index=False)
lob_df.to_csv(out("lob_data.csv"), index=False)
sen_df.to_csv(out("senrep_data.csv"), index=False)
print(f"  V CSVs saved to {OUT_DIR}")

if len(uas_records) < 5:
    print("\n  ! Not enough UAS fixes for ML analysis (need 5+).")
    print("    Make sure the simulator is running and sensors are detecting.")
    print("    Try again in a minute or two.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════
#  STEP 3: FOLIUM INTERACTIVE MAP
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  Building interactive Folium map...")
print("=" * 60)

sensors = {
    "AZ-MA-1": (31.6490196, -110.2758537),
    "AZ-MA-2": (31.6569236, -110.2659979),
    "AZ-MA-3": (31.6637961, -110.2515496),
}

m = folium.Map(location=[31.658, -110.270], zoom_start=13)

# Sensor nodes
for name, (lat, lon) in sensors.items():
    folium.CircleMarker(
        [lat, lon], radius=10, color="blue",
        fill=True, fill_color="blue",
        popup=name, tooltip=name
    ).add_to(m)

# UAS track
track_points = []
for _, row in uas_df.iterrows():
    lat = row.get("estimatedLat")
    lon = row.get("estimatedLon")
    if pd.notna(lat) and pd.notna(lon):
        track_points.append((float(lat), float(lon)))
        folium.CircleMarker(
            [float(lat), float(lon)], radius=4,
            color="red", fill=True, fill_color="red", fill_opacity=0.4,
            tooltip=str(row.get("phenomenonTime", ""))
        ).add_to(m)

if len(track_points) > 1:
    folium.PolyLine(track_points, color="red", weight=2, opacity=0.6).add_to(m)

if track_points:
    folium.Marker(
        track_points[-1],
        icon=folium.Icon(color="red", icon="plane"),
        tooltip="Latest UAS Position"
    ).add_to(m)

# LOB lines
for _, row in lob_df.iterrows():
    bearing = row.get("bearingTrue")
    slat = row.get("sensorLat")
    slon = row.get("sensorLon")
    if pd.notna(bearing) and pd.notna(slat) and pd.notna(slon):
        dist = 0.05
        end_lat = float(slat) + dist * math.cos(math.radians(float(bearing)))
        end_lon = float(slon) + dist * math.sin(math.radians(float(bearing)))
        folium.PolyLine(
            [[float(slat), float(slon)], [end_lat, end_lon]],
            color="orange", weight=1.5, dash_array="6",
            tooltip=f"{row.get('sensor','')} LOB {bearing}°"
        ).add_to(m)

# SENREPs
for _, row in sen_df.iterrows():
    lat = row.get("etaLat")
    lon = row.get("etaLon")
    if pd.notna(lat) and pd.notna(lon) and lat != "" and lon != "":
        folium.Marker(
            [float(lat), float(lon)],
            icon=folium.Icon(color="orange", icon="flag"),
            tooltip=str(row.get("title", "SENREP"))
        ).add_to(m)

map_path = out("csapi_live_map.html")
m.save(map_path)
print(f"  V Interactive map saved: {map_path}")

# ═══════════════════════════════════════════════════════════════════
#  STEP 4: INTELLIGENCE DASHBOARD (matplotlib)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  Generating intelligence dashboard...")
print("=" * 60)

uas = pd.read_csv(out("uas_track.csv"), parse_dates=["phenomenonTime"])
lob = pd.read_csv(out("lob_data.csv"), parse_dates=["phenomenonTime"])
sen = pd.read_csv(out("senrep_data.csv"), parse_dates=["phenomenonTime"])
uas = uas.sort_values("phenomenonTime").reset_index(drop=True)
lob = lob.sort_values("phenomenonTime").reset_index(drop=True)

DARK = "#0d1117"; PANEL = "#161b22"
BLUE = "#2E75B6"; RED = "#e74c3c"
ORG = "#f39c12"; GRN = "#2ecc71"
WHT = "#ffffff"; GRY = "#8b949e"

def style_ax(ax, title):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=GRY, labelsize=8)
    ax.title.set_color(WHT); ax.title.set_fontsize(10); ax.title.set_fontweight("bold")
    ax.set_title(title)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    ax.xaxis.label.set_color(GRY); ax.yaxis.label.set_color(GRY)

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor(DARK)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 1. UAS Flight Track
ax1 = fig.add_subplot(gs[0:2, 0:2])
style_ax(ax1, "UAS Flight Track")
for name, (lat, lon) in sensors.items():
    ax1.scatter(lon, lat, s=150, color=BLUE, zorder=5, marker="^")
    ax1.annotate(name, (lon, lat), textcoords="offset points",
                 xytext=(5, 5), color=BLUE, fontsize=8)
ax1.plot(uas["estimatedLon"], uas["estimatedLat"], color=RED, linewidth=1.5, alpha=0.6, zorder=3)
sc = ax1.scatter(uas["estimatedLon"], uas["estimatedLat"],
                 c=range(len(uas)), cmap="YlOrRd", s=50, zorder=4, label="UAS positions")
if not sen.empty and "etaLon" in sen.columns and "etaLat" in sen.columns:
    valid_sen = sen.dropna(subset=["etaLon", "etaLat"])
    if not valid_sen.empty:
        ax1.scatter(valid_sen["etaLon"], valid_sen["etaLat"],
                    s=250, color=ORG, marker="*", zorder=6, label="SENREPs")

all_lons = list(uas["estimatedLon"]) + [v[1] for v in sensors.values()]
all_lats = list(uas["estimatedLat"]) + [v[0] for v in sensors.values()]
pad_lon = (max(all_lons) - min(all_lons)) * 0.15 + 0.002
pad_lat = (max(all_lats) - min(all_lats)) * 0.15 + 0.002
ax1.set_xlim(min(all_lons) - pad_lon, max(all_lons) + pad_lon)
ax1.set_ylim(min(all_lats) - pad_lat, max(all_lats) + pad_lat)
cb = plt.colorbar(sc, ax=ax1)
cb.set_label("Time progression ->", color=GRY, fontsize=8)
cb.ax.yaxis.set_tick_params(color=GRY, labelcolor=GRY)
ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
ax1.legend(loc="upper right", fontsize=8, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)

# 2. Bearing Over Time
ax2 = fig.add_subplot(gs[0, 2])
style_ax(ax2, "LOB Bearing Over Time")
colors_s = {"AZ-MA-1": BLUE, "AZ-MA-2": GRN, "AZ-MA-3": ORG}
for sensor, grp in lob.groupby("sensor"):
    ax2.plot(grp["phenomenonTime"], grp["bearingTrue"],
             label=sensor, color=colors_s.get(sensor, WHT), linewidth=1.5, alpha=0.9)
ax2.set_ylabel("Bearing (deg)")
ax2.legend(fontsize=7, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# 3. Bearing Std Dev
ax3 = fig.add_subplot(gs[1, 2])
style_ax(ax3, "LOB Uncertainty (Std Dev)")
for sensor, grp in lob.groupby("sensor"):
    ax3.plot(grp["phenomenonTime"], grp["bearingStdDev"],
             label=sensor, color=colors_s.get(sensor, WHT), linewidth=1.5, alpha=0.9)
ax3.set_ylabel("Std Dev (deg)")
ax3.legend(fontsize=7, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# 4. Latitude over time
ax4 = fig.add_subplot(gs[2, 0])
style_ax(ax4, "UAS Latitude Over Time")
ax4.plot(uas["phenomenonTime"], uas["estimatedLat"], color=RED, linewidth=2)
ax4.fill_between(uas["phenomenonTime"], uas["estimatedLat"],
                 uas["estimatedLat"].min(), alpha=0.2, color=RED)
ax4.set_ylabel("Latitude")
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# 5. Longitude over time
ax5 = fig.add_subplot(gs[2, 1])
style_ax(ax5, "UAS Longitude Over Time")
ax5.plot(uas["phenomenonTime"], uas["estimatedLon"], color=ORG, linewidth=2)
ax5.fill_between(uas["phenomenonTime"], uas["estimatedLon"],
                 uas["estimatedLon"].min(), alpha=0.2, color=ORG)
ax5.set_ylabel("Longitude")
plt.setp(ax5.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# 6. Contributing sensors
ax6 = fig.add_subplot(gs[2, 2])
style_ax(ax6, "LOBs Contributing per Fix")
bar_colors = [GRN if n == 3 else ORG if n == 2 else RED for n in uas["numContributingLobs"]]
ax6.bar(range(len(uas)), uas["numContributingLobs"], color=bar_colors, edgecolor=DARK, width=0.8)
ax6.set_ylabel("# Sensors"); ax6.set_xlabel("Fix #")
ax6.set_yticks([1, 2, 3]); ax6.set_ylim(0, 3.5)
ax6.axhline(3, color=GRN, linewidth=0.8, linestyle="--", alpha=0.5)

stats = (
    f"Track: C-20260305-SLB-001\n"
    f"Fixes: {len(uas)}  |  LOBs: {len(lob)}  |  SENREPs: {len(sen)}\n"
    f"Lat range: {round(uas['estimatedLat'].min(),4)} -> {round(uas['estimatedLat'].max(),4)}\n"
    f"Sensors: AZ-MA-1, AZ-MA-2, AZ-MA-3"
)
fig.text(0.01, 0.01, stats, color=GRY, fontsize=8, verticalalignment="bottom",
         bbox=dict(facecolor=PANEL, edgecolor="#30363d", boxstyle="round,pad=0.4"))

fig.suptitle(
    "CSAPI Live Intelligence Dashboard  |  Classification: UAS  |  " +
    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    color=WHT, fontsize=13, fontweight="bold", y=0.99)

dash_path = out("csapi_dashboard.png")
plt.savefig(dash_path, dpi=150, bbox_inches="tight", facecolor=DARK)
plt.close()
print(f"  V Dashboard saved: {dash_path}")

# ═══════════════════════════════════════════════════════════════════
#  STEP 5: ML ANALYSIS — Anomaly Detection + Trajectory Prediction
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  Running ML analysis (Isolation Forest + Trajectory Prediction)...")
print("=" * 60)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

# Feature engineering
uas["dist_m"] = 0.0; uas["speed_ms"] = 0.0; uas["heading"] = 0.0
for i in range(1, len(uas)):
    dist = haversine(
        uas.loc[i-1, "estimatedLat"], uas.loc[i-1, "estimatedLon"],
        uas.loc[i, "estimatedLat"], uas.loc[i, "estimatedLon"])
    dt = (uas.loc[i, "phenomenonTime"] - uas.loc[i-1, "phenomenonTime"]).total_seconds()
    uas.loc[i, "dist_m"] = dist
    uas.loc[i, "speed_ms"] = dist / dt if dt > 0 else 0
    dlon = uas.loc[i, "estimatedLon"] - uas.loc[i-1, "estimatedLon"]
    dlat = uas.loc[i, "estimatedLat"] - uas.loc[i-1, "estimatedLat"]
    uas.loc[i, "heading"] = (np.degrees(np.arctan2(dlon, dlat)) + 360) % 360

uas["heading_change"] = uas["heading"].diff().fillna(0).abs().apply(lambda x: min(x, 360 - x))
uas["sensor_count"] = uas["numContributingLobs"]

print(f"  Features: speed_ms, heading, heading_change, dist_m, sensor_count")
print(f"  Avg speed: {uas['speed_ms'].mean():.2f} m/s")
print(f"  Max speed: {uas['speed_ms'].max():.2f} m/s")

# Isolation Forest
features = uas[["speed_ms", "heading_change", "dist_m", "sensor_count"]].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)
iso = IsolationForest(contamination=0.15, random_state=42)
uas["anomaly"] = iso.fit_predict(X_scaled)
uas["anomaly_score"] = iso.decision_function(X_scaled)
anomalies = uas[uas["anomaly"] == -1]
normal = uas[uas["anomaly"] == 1]
print(f"  Anomalies detected: {len(anomalies)} / {len(uas)} fixes")

# Trajectory prediction
last5 = uas.tail(5)
avg_dlat = last5["estimatedLat"].diff().mean()
avg_dlon = last5["estimatedLon"].diff().mean()
pred = []
lat, lon = uas["estimatedLat"].iloc[-1], uas["estimatedLon"].iloc[-1]
for _ in range(5):
    lat += avg_dlat; lon += avg_dlon
    pred.append((lat, lon))
pred_df = pd.DataFrame(pred, columns=["predLat", "predLon"])
print(f"  Predicted next position: ({pred[0][0]:.5f}, {pred[0][1]:.5f})")

# ML Dashboard
PRP = "#9b59b6"
fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor(DARK)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# Panel 1: Track + Anomalies + Prediction
ax1 = fig.add_subplot(gs[0:2, 0:2])
style_ax(ax1, "UAS Track - Anomaly Detection + Trajectory Prediction")
ax1.scatter(normal["estimatedLon"], normal["estimatedLat"],
            color=GRN, s=50, zorder=4, label="Normal fix")
ax1.scatter(anomalies["estimatedLon"], anomalies["estimatedLat"],
            color=RED, s=120, marker="X", zorder=5, label="ANOMALY")
ax1.plot(uas["estimatedLon"], uas["estimatedLat"],
         color=GRY, linewidth=1, alpha=0.4, zorder=3)
ax1.plot(pred_df["predLon"], pred_df["predLat"],
         color=PRP, linewidth=2, linestyle="--", alpha=0.8, zorder=4, label="Predicted track")
ax1.scatter(pred_df["predLon"], pred_df["predLat"],
            color=PRP, s=60, marker="D", zorder=5)
ax1.annotate("",
    xy=(pred_df["predLon"].iloc[-1], pred_df["predLat"].iloc[-1]),
    xytext=(uas["estimatedLon"].iloc[-1], uas["estimatedLat"].iloc[-1]),
    arrowprops=dict(arrowstyle="->", color=PRP, lw=2))
for name, (slat, slon) in sensors.items():
    ax1.scatter(slon, slat, s=150, color=BLUE, zorder=5, marker="^")
    ax1.annotate(name, (slon, slat), textcoords="offset points",
                 xytext=(5, 5), color=BLUE, fontsize=7)
all_lons2 = list(uas["estimatedLon"]) + list(pred_df["predLon"]) + [v[1] for v in sensors.values()]
all_lats2 = list(uas["estimatedLat"]) + list(pred_df["predLat"]) + [v[0] for v in sensors.values()]
pad = 0.003
ax1.set_xlim(min(all_lons2)-pad, max(all_lons2)+pad)
ax1.set_ylim(min(all_lats2)-pad, max(all_lats2)+pad)
ax1.legend(loc="upper right", fontsize=8, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)
ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")

# Panel 2: Speed
ax2 = fig.add_subplot(gs[0, 2])
style_ax(ax2, "Speed Over Time (m/s)")
ax2.plot(uas["phenomenonTime"], uas["speed_ms"], color=GRN, linewidth=1.5)
ax2.scatter(anomalies["phenomenonTime"], anomalies["speed_ms"],
            color=RED, s=80, marker="X", zorder=5, label="Anomaly")
ax2.axhline(uas["speed_ms"].mean(), color=ORG, linestyle="--", linewidth=1, label="Mean speed")
ax2.set_ylabel("Speed (m/s)")
ax2.legend(fontsize=7, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# Panel 3: Turn rate
ax3 = fig.add_subplot(gs[1, 2])
style_ax(ax3, "Turn Rate (Heading Change deg)")
ax3.plot(uas["phenomenonTime"], uas["heading_change"], color=ORG, linewidth=1.5)
ax3.scatter(anomalies["phenomenonTime"], anomalies["heading_change"],
            color=RED, s=80, marker="X", zorder=5, label="Anomaly")
ax3.set_ylabel("Turn (deg)")
ax3.legend(fontsize=7, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=6)

# Panel 4: Anomaly score
ax4 = fig.add_subplot(gs[2, 0])
style_ax(ax4, "Anomaly Score Over Time")
colors_a = [RED if a == -1 else GRN for a in uas["anomaly"]]
ax4.bar(range(len(uas)), uas["anomaly_score"], color=colors_a, edgecolor=DARK, width=0.8)
ax4.axhline(0, color=WHT, linewidth=0.5, linestyle="--", alpha=0.4)
ax4.set_xlabel("Fix #"); ax4.set_ylabel("Score (lower = more anomalous)")

# Panel 5: Speed histogram
ax5 = fig.add_subplot(gs[2, 1])
style_ax(ax5, "Speed Distribution")
ax5.hist(normal["speed_ms"], bins=10, color=GRN, alpha=0.7, label="Normal", edgecolor=DARK)
ax5.hist(anomalies["speed_ms"], bins=5, color=RED, alpha=0.7, label="Anomaly", edgecolor=DARK)
ax5.set_xlabel("Speed (m/s)"); ax5.set_ylabel("Count")
ax5.legend(fontsize=7, facecolor=PANEL, labelcolor=WHT, edgecolor=GRY)

# Panel 6: Summary stats
ax6 = fig.add_subplot(gs[2, 2])
style_ax(ax6, "Detection Summary")
ax6.axis("off")
summary = [
    ("Total fixes", str(len(uas))),
    ("Normal fixes", str(len(normal))),
    ("Anomalies detected", str(len(anomalies))),
    ("Avg speed", f"{uas['speed_ms'].mean():.2f} m/s"),
    ("Max speed", f"{uas['speed_ms'].max():.2f} m/s"),
    ("Avg turn rate", f"{uas['heading_change'].mean():.1f} deg"),
    ("Max turn", f"{uas['heading_change'].max():.1f} deg"),
    ("Predicted lat", f"{pred[0][0]:.5f}"),
    ("Predicted lon", f"{pred[0][1]:.5f}"),
]
for i, (label, value) in enumerate(summary):
    y = 0.92 - i * 0.10
    ax6.text(0.02, y, label + ":", color=GRY, fontsize=9, transform=ax6.transAxes)
    color = RED if "Anomal" in label and len(anomalies) > 0 else WHT
    ax6.text(0.55, y, value, color=color, fontsize=9, fontweight="bold", transform=ax6.transAxes)

fig.suptitle(
    "CSAPI ML Analysis  |  Isolation Forest Anomaly Detection  |  Trajectory Prediction",
    color=WHT, fontsize=12, fontweight="bold", y=0.99)

ml_path = out("csapi_ml_dashboard.png")
plt.savefig(ml_path, dpi=150, bbox_inches="tight", facecolor=DARK)
plt.close()
print(f"  V ML dashboard saved: {ml_path}")

# ═══════════════════════════════════════════════════════════════════
#  DONE
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ALL OUTPUTS GENERATED")
print("=" * 60)
print(f"  1. {out('csapi_live_map.html')}     <- open in browser")
print(f"  2. {out('csapi_dashboard.png')}      <- intelligence dashboard")
print(f"  3. {out('csapi_ml_dashboard.png')}   <- ML anomaly + prediction")
print(f"  4. {out('uas_track.csv')}            <- raw UAS fixes")
print(f"  5. {out('lob_data.csv')}             <- raw LOB data")
print(f"  6. {out('senrep_data.csv')}          <- raw SENREP data")
print("=" * 60)
