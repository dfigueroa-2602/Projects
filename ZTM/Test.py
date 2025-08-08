import requests
import folium
import time
from datetime import datetime, timedelta

API_KEY = "9af7f84a-c699-4d86-82bf-9dce1d68d5cc"
STOP_DATASET_ID = "ab75c33d-3a26-4342-b36a-6e5fef0a3ac3"
LINES_LIST_ID = "88cd555f-6f31-43ca-9de4-66c479ad5942"
SCHEDULE_ID = "e923fa0e-d96c-43f9-ae6e-60518c9f3238"

def fetch_vehicle_positions_for_line(line_id) -> list:
    response = requests.get("https://mkuran.pl/map/", params={"line": line_id})
    return response.json().get("vehicles", [])

fetch_vehicle_positions_for_line(153)

def search_unique_stop_by_name(name, max_pages=50):
    url = "https://api.um.warszawa.pl/api/action/dbstore_get"
    found = {}
    
    for page in range(1, max_pages + 1):
        params = {
            "id": STOP_DATASET_ID,
            "apikey": API_KEY,
            "page": page,
            "size": 100
        }

        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("result", [])

        if not results:
            break

        for stop in results:
            values = {item["key"]: item["value"] for item in stop["values"]}
            stop_name = values.get("nazwa_zespolu", "").lower()

            if name.lower() in stop_name:
                key = (values["zespol"], values["slupek"])
                if key not in found:
                    found[key] = values

    return list(found.values())


def get_bus_lines_for_stop(zespol, slupek):
    url = "https://api.um.warszawa.pl/api/action/dbtimetable_get"
    params = {
        "id": LINES_LIST_ID,
        "busstopId": zespol,
        "busstopNr": slupek,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)

    try:
        data = response.json()
        results = data.get("result", [])
        lines = set()

        for record in results:
            for val in record["values"]:
                if val["key"] == "linia":
                    lines.add(val["value"])

        return sorted(lines)

    except Exception as e:
        print(f"Error retrieving lines for stop {zespol}/{slupek}:", e)
        return []


def get_timetable_for_line(zespol, slupek, line):
    url = "https://api.um.warszawa.pl/api/action/dbtimetable_get"
    params = {
        "id": SCHEDULE_ID,
        "busstopId": zespol,
        "busstopNr": slupek,
        "line": line,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)

    try:
        data = response.json()
        results = data.get("result", [])

        times = []

        for entry in results:
            # Each entry is a list of dicts like {'key': ..., 'value': ...}
            for field in entry:
                if field["key"] == "czas":
                    times.append(field["value"])

        return sorted(times)

    except Exception as e:
        print(f"Error retrieving timetable for line {line} at stop {zespol}/{slupek}:", e)
        print("Raw response:")
        print(response.text)
        return []

def print_next_departures(schedule, now=None, count=4):
    if not schedule:
        print("No timetable available.")
        return

    if now is None:
        now = datetime.now()

    # Extract today's times
    upcoming = []
    for time_str in schedule:
        hour, minute, second = map(int, time_str.split(":"))
        dep_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

        # Handle times that already passed by assuming next day
        if dep_time < now:
            dep_time += timedelta(days=1)

        minutes_left = int((dep_time - now).total_seconds() // 60)
        upcoming.append((time_str, minutes_left))

    # Sort just in case (should be already sorted)
    upcoming.sort(key=lambda x: x[1])

    # Print next `count` departures
    print(f"\n⏰ The next {count} departures are:")
    for time_str, minutes_left in upcoming[:count]:
        print(f"🕒 {time_str} — in {minutes_left} min{'s' if minutes_left != 1 else ''}")

def plot_stops_on_map(stops, map_filename="map.html"):
    if not stops:
        print("No stops to plot.")
        return

    lat_center = float(stops[0]["szer_geo"])
    lon_center = float(stops[0]["dlug_geo"])
    m = folium.Map(location=[lat_center, lon_center], zoom_start=15)

    for stop in stops:
        name = stop.get("nazwa_zespolu", "Unknown")
        direction = stop.get("kierunek", "")
        zespol = stop.get("zespol")
        slupek = stop.get("slupek")
        lat = float(stop["szer_geo"])
        lon = float(stop["dlug_geo"])
        lines = get_bus_lines_for_stop(zespol, slupek)

        label = (
            f"<b>{name} ({zespol}/{slupek})</b><br>"
            f"Direction: {direction}<br>"
            f"Lines: {', '.join(lines) if lines else 'None'}"
        )

        folium.Marker(
            location=[lat, lon],
            popup=label,
            icon=folium.Icon(color="blue", icon="bus", prefix="fa")
        ).add_to(m)

    m.save(map_filename)
    print(f"Map saved to: {map_filename}")


# === MAIN EXECUTION ===

search_name = input("Enter the bus stop name to search: ").strip()
stops = search_unique_stop_by_name(search_name)

if not stops:
    print(f"No stops found with the name '{search_name}'.")
    exit()

print(f"\nFound {len(stops)} stop variant(s):\n")
for i, stop in enumerate(stops):
    print(f"{i+1}. {stop['nazwa_zespolu']} ({stop['zespol']}/{stop['slupek']}) → {stop['kierunek']}")

selected_index = int(input("\nSelect a stop number: ")) - 1
selected_stop = stops[selected_index]

zespol = selected_stop["zespol"]
slupek = selected_stop["slupek"]

lines = get_bus_lines_for_stop(zespol, slupek)

if not lines:
    print("No bus lines found at this stop.")
    exit()

print(f"\nLines at stop {zespol}/{slupek}:")
for i, line in enumerate(lines):
    print(f"{i+1}. {line}")

line_input = input("\nSelect a line number (e.g. 1 or 153): ").strip()

# If user typed a number like '1' for index
if line_input.isdigit() and 1 <= int(line_input) <= len(lines):
    selected_line = lines[int(line_input) - 1]

# If user typed the actual line code like '153' or 'N24'
elif line_input in lines:
    selected_line = line_input

else:
    print("❌ Invalid input. Please run again and enter a valid index or bus line.")
    exit()

schedule = get_timetable_for_line(zespol, slupek, selected_line)

print(f"\n🚌 Timetable for line {selected_line} at stop {selected_stop['nazwa_zespolu']} ({zespol}/{slupek}):")
if schedule:
    for t in schedule:
        print("🕒", t)
else:
    print("No schedule available.")

schedule = get_timetable_for_line(zespol, slupek, selected_line)

if schedule:
    # Show next 4 departures
    print_next_departures(schedule)
else:
    print("No schedule available.")

def live_map_for_line(selected_line):
    m = folium.Map(location=[52.2297, 21.0122], zoom_start=13)  # center Warsaw

    # Add a JavaScript timer to refresh every 15–30 seconds
    js = f"""
    function update() {{
      fetch('http://localhost:8000/vehicles/{line}')
        .then(res => res.json())
        .then(data => {{
          // Update vehicle markers here (requires custom JS)
        }});
    }}
    setInterval(update, 20000);
    """
    m.get_root().html.add_child(folium.Element(f"<script>{js}</script>"))
    m.save("live_map.html")
    print("Live map created: open live_map.html in your browser.")

# Optional map generation
plot = input("\nGenerate map with all matching stops? (y/n): ").strip().lower()
if plot == 'y':
    plot_stops_on_map(stops)
