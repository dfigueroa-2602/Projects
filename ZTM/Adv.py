import requests
import folium
import webbrowser
import os
import time

# === Configuration ===
LINE_NUMBER = "143"
REFRESH_INTERVAL = 5  # seconds
MAP_FILENAME = "bus_map.html"
AUTO_OPEN_ONCE = True


def fetch_live_positions():
    url = "https://mkuran.pl/gtfs/warsaw/vehicles.json"
    response = requests.get(url)
    data = response.json()
    return data["positions"]


def find_line_vehicles(positions, line_number):
    return [
        pos for pos in positions
        if pos["trip_id"].split(":")[1] == line_number
    ]


def plot_initial_map(vehicles, line_number, map_filename):
    if not vehicles:
        print(f"⚠️ No vehicles found for line {line_number}")
        return

    lat_center = vehicles[0]["lat"]
    lon_center = vehicles[0]["lon"]
    m = folium.Map(location=[lat_center, lon_center], zoom_start=13)

    folium.TileLayer('OpenStreetMap').add_to(m)

    # ❌ Don't add any markers here – JS will do it
    m.save(map_filename)
    print(f"✅ Initial map with base layers saved as '{map_filename}'")



def inject_js_live_update(filename, line_number="143", interval=5):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            html = f.read()

        js_patch = f"""
<script>
// Wait for Leaflet map to be available
let map = null;
let tryInit = setInterval(() => {{
    if (typeof window.L === 'undefined') return;

    const maps = Object.values(window).filter(v => v instanceof L.Map);
    if (maps.length > 0) {{
        map = maps[0];
        clearInterval(tryInit);
        startTracking();
    }}
}}, 500);

let markers = [];

function startTracking() {{
    async function update() {{
        try {{
            const response = await fetch("https://corsproxy.io/?https://mkuran.pl/gtfs/warsaw/vehicles.json");
            const data = await response.json();

            markers.forEach(m => map.removeLayer(m));
            markers = [];
            const newMarkers = [];                                                    

            const vehicles = data.positions.filter(p => p.trip_id.split(":")[1] === "{line_number}");
            vehicles.forEach(p => {{

                const existing = markers.find(m => m.options.trip_id === p.trip_id);

                if (existing) {{
                    existing.setLatLng([p.lat, p.lon]);

                    const iconEl = existing.getElement();
                    if (iconEl) {{
                        iconEl.style.transition = "transform 1s ease";
                        iconEl.style.transform = "scale(1.1)";
                        setTimeout(() => iconEl.style.transform = "scale(1)", 200);
                    }}

                    newMarkers.push(existing);
                }} else {{
            
                const marker = L.marker([p.lat, p.lon], {{
                    icon: L.AwesomeMarkers.icon({{
                        icon: 'bus',
                        prefix: 'fa',
                        markerColor: 'red'
                    }})
                }}).bindPopup(`
                
<b>🚌 Line: {line_number}</b><br>
🆔 Trip: ${{p.trip_id}}<br>
🔢 Bus ID: ${{p.side_number ?? "N/A"}}<br>
🧭 Bearing: ${{p.bearing ?? "N/A"}}<br>
🕒 ${{p.timestamp}}<br>
📍 ${{p.lat}}, ${{p.lon}}
                `);
                marker.addTo(map);
                    newMarkers.push(marker);
                }}
            }});

            markers.forEach(m => {{
                if (!newMarkers.includes(m)) {{
                    map.removeLayer(m);
                }}
            }});
            markers = newMarkers;

            
            console.log("✅ Bus positions updated.");
        }} catch (err) {{
            console.error("❌ Failed to update positions:", err);
        }}
    }}

    update();
    setInterval(update, {interval * 1000});
}}
</script>
</body>
"""

        if "</body>" in html:
            html = html.replace("</body>", js_patch)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            print("✅ JavaScript injected successfully.")
        else:
            print("❌ <body> tag not found in HTML.")

    except Exception as e:
        print("❌ JS injection error:", e)



# === MAIN EXECUTION ===

print(f"🛰️ Generating live bus tracker for line {LINE_NUMBER}...\n")

positions = fetch_live_positions()
vehicles = find_line_vehicles(positions, LINE_NUMBER)

if not vehicles:
    print(f"❌ No active buses found for line {LINE_NUMBER}.")
    exit()

plot_initial_map(vehicles, LINE_NUMBER, MAP_FILENAME)
inject_js_live_update(MAP_FILENAME, line_number=LINE_NUMBER, interval=REFRESH_INTERVAL)

if AUTO_OPEN_ONCE:
    webbrowser.open(f"file://{os.path.abspath(MAP_FILENAME)}")
