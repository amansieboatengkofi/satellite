import requests
import json
import ee
import folium
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
from branca.colormap import LinearColormap
from datetime import datetime, timedelta
import time
import numpy as np
import rasterio
from rasterio.io import MemoryFile

# Initialize Google Earth Engine
ee.Initialize(project='ee-amansieboatengkofi')

# Historical NDWI data storage
HISTORICAL_DATA_FILE = "pra_river_ndwi_historical_data.json"
try:
    with open(HISTORICAL_DATA_FILE, 'r') as file:
        historical_data = json.load(file)
except FileNotFoundError:
    historical_data = {}

def save_historical_data(data):
    with open(HISTORICAL_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Fetch river geometry using Overpass API
def fetch_river_by_relation_id(relation_id):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"[out:json]; relation({relation_id}); (._;>;); out geom;"
    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise ValueError(f"Error fetching data: {response.status_code}")
    return [LineString([(pt['lon'], pt['lat']) for pt in element['geometry']])
            for element in response.json()['elements']
            if element['type'] == 'way']

def gdf_to_ee_geometry(lines):
    merged = linemerge(lines)
    if isinstance(merged, MultiLineString):
        merged = max(merged.geoms, key=lambda g: g.length)
    return ee.Geometry.LineString(list(merged.coords))

def generate_clipped_grid(geometry, grid_size=0.04):
    bbox = geometry.bounds().coordinates().getInfo()[0]
    xmin, ymin = bbox[0][0], bbox[0][1]
    xmax, ymax = bbox[2][0], bbox[2][1]

    grid = []
    x = xmin
    while x < xmax:
        y = ymin
        while y < ymax:
            cell_geometry = ee.Geometry.Rectangle([x, y, x + grid_size, y + grid_size])
            clipped_geometry = cell_geometry.intersection(geometry, 1)
            if clipped_geometry.area().getInfo() > 0:  # Keep only non-empty cells
                grid.append({
                    "geometry": clipped_geometry,
                    "bounds": [x, y, x + grid_size, y + grid_size]
                })
            y += grid_size
        x += grid_size
    return grid

def generate_satellite_image_url(bounds, river_geometry, api_key):
    bbox = ee.Geometry.Rectangle(bounds)
    river_section = river_geometry.intersection(bbox)

    try:
        coordinates = river_section.coordinates().getInfo()
        if coordinates and isinstance(coordinates[0], list):
            lon, lat = coordinates[0][0][0], coordinates[0][1][1]
        else:
            raise ValueError("No valid river coordinates found.")
    except Exception:
        lon = (bounds[0] + bounds[2]) / 2
        lat = (bounds[1] + bounds[3]) / 2

    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=17&size=400x400&maptype=satellite&key={api_key}"

def update_historical_data(section_name, date, mean_ndwi):
    section_history = historical_data.get(section_name, {}).get('history', [])
    # Keep only the last 30 days of history
    section_history = [entry for entry in section_history
                       if (datetime.now() - datetime.strptime(entry['date'], '%Y-%m-%d')).days <= 30]
    # Add the new entry if not already present
    if not any(entry['date'] == date for entry in section_history):
        section_history.append({'date': date, 'ndwi': mean_ndwi})
    historical_data[section_name] = {'history': section_history}

# --- Planet Labs NDWI computation functions ---
def get_ndwi_planet(start_date, end_date, cell_geometry, planet_api_key):
    """
    For the given date window [start_date, end_date] (YYYY-MM-DD strings) and
    cell_geometry (an ee.Geometry), search Planet Labs for a PSScene image with low cloud cover
    that intersects the cell. Then download the 4-band analytic asset (basic_analytic_4b),
    compute NDWI = (Green - NIR) / (Green + NIR) over only the water pixels and return the mean NDWI.
    """
    # Convert ee.Geometry to GeoJSON dictionary
    try:
        geometry_geojson = cell_geometry.getInfo()
    except Exception as e:
        print("Error converting ee.Geometry to GeoJSON:", e)
        return None

    # Debug: print the GeoJSON geometry
    print("DEBUG: Requesting imagery for grid cell geometry:")
    print(json.dumps(geometry_geojson, indent=2))

    # Convert dates to full ISO 8601 format.
    start_datetime = f"{start_date}T00:00:00.000Z"
    end_datetime = f"{end_date}T23:59:59.999Z"

    search_payload = {
       "item_types": ["PSScene"],
       "filter": {
         "type": "AndFilter",
         "config": [
             {"type": "GeometryFilter", "field_name": "geometry", "config": geometry_geojson},
             {"type": "DateRangeFilter", "field_name": "acquired",
              "config": {"gte": start_datetime, "lte": end_datetime}},
             {"type": "RangeFilter", "field_name": "cloud_cover", "config": {"lte": 0.2}},
             {"type": "PermissionFilter", "config": ["assets:download"]}
         ]
       }
    }

    #print('Planet search payload:', json.dumps(search_payload, indent=2))
    search_url = "https://api.planet.com/data/v1/quick-search"
    response = requests.post(search_url, auth=(planet_api_key, ''), json=search_payload)
    if response.status_code != 200:
         print(f"Planet search error: {response.status_code}")
         return None
    results = response.json().get("features", [])
    if not results:
         # No image available for this day and cell.
         return None
    # Pick the first available image
    feature = results[0]
    item_id = feature["id"]
    item_type = feature["properties"]["item_type"]

    # Get the available assets for the image
    assets_url = f"https://api.planet.com/data/v1/item-types/{item_type}/items/{item_id}/assets"
    assets_response = requests.get(assets_url, auth=(planet_api_key, ''))
    if assets_response.status_code != 200:
         print(f"Error fetching asset info: {assets_response.status_code}")
         return None
    assets = assets_response.json()
    if "basic_analytic_4b" not in assets:
         print("basic_analytic_4b asset not available for this item.")
         return None
    analytic_asset = assets["basic_analytic_4b"]
    if analytic_asset["status"] != "active":
         activate_url = analytic_asset["_links"]["activate"]
         act_response = requests.post(activate_url, auth=(planet_api_key, ''))
         if act_response.status_code != 200:
             print("Error activating asset.")
             return None
         time.sleep(5)  # Wait for activation (in production, poll until active)
         assets_response = requests.get(assets_url, auth=(planet_api_key, ''))
         assets = assets_response.json()
         analytic_asset = assets.get("basic_analytic_4b", {})
         if analytic_asset.get("status") != "active":
             print("Asset still not active.")
             return None

    image_url = analytic_asset["location"]
    img_response = requests.get(image_url)
    if img_response.status_code != 200:
         print("Error downloading analytic image.")
         return None
    try:
        with MemoryFile(img_response.content) as memfile:
            with memfile.open() as dataset:
                # For PSScene, bands are typically:
                # Band 1: Blue, Band 2: Green, Band 3: Red, Band 4: NIR
                green = dataset.read(2).astype('float32')
                nir = dataset.read(4).astype('float32')
                # Calculate NDWI per pixel
                ndwi = (green - nir) / (green + nir + 1e-10)
                # Create a water mask. Here we assume pixels with NDWI > 0 are water.
                water_mask = ndwi > -0.3
                if np.sum(water_mask) == 0:
                    # No water pixels found.
                    return None
                # Compute the mean NDWI only over water pixels
                mean_ndwi = float(np.nanmean(ndwi[water_mask]))
                return mean_ndwi
    except Exception as e:
        print("Error processing TIFF image:", e)
        return None

# --- End Planet Labs functions ---

# Define the rivers to process (update relation id for Pra River)
relation_ids = {
    'Pra River': 5250354,
}

# Fetch Pra River geometry for map centering
pra_geometry_lines = fetch_river_by_relation_id(relation_ids['Pra River'])
pra_coordinates = gdf_to_ee_geometry(pra_geometry_lines).coordinates().getInfo()
pra_center = pra_coordinates[len(pra_coordinates) // 2]  # Approximate center of the river

# Initialize the folium map
my_map = folium.Map(location=[pra_center[1], pra_center[0]], zoom_start=10)

# Define grid_size before using it
grid_size = 0.04  # Adjust the grid size as needed

# NDWI Visualization Parameters:
ndwi_vis_params = {'min': -1, 'max': 1, 'palette': ['black', 'yellow', 'blue']}
colormap = LinearColormap(['black', 'yellow', 'blue'], vmin=-1, vmax=1)

# Your API keys: Google Maps API key and Planet Labs API key
google_maps_api_key = "AIzaSyBaraoG9hMuLfTdTqMBvwHcWzjvDeDBNYo"
planet_api_key = "PLAKf375b8911e104a0f997f32e438d070e3"  # Replace with your actual Planet Labs API key

# Threshold for a dramatic drop in NDWI
DRAMATIC_DROP_THRESHOLD = 0.05

for river_name, relation_id in relation_ids.items():
    print(f"Processing {river_name}...")
    try:
        river_lines = fetch_river_by_relation_id(relation_id)
        ee_geometry = gdf_to_ee_geometry(river_lines).buffer(1)

        # Generate a grid covering the river area
        grid_cells = generate_clipped_grid(ee_geometry, grid_size)

        # Process each grid cell individually
        for idx, cell in enumerate(grid_cells):
            cell_geometry = cell["geometry"]
            bounds = cell["bounds"]
            section_name = f"{river_name} - Grid {idx + 1}"

            # Update historical data for the last 30 days for this grid cell.
            for day_offset in range(30, -1, -1):
                current_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
                next_date = (datetime.now() - timedelta(days=day_offset - 1)).strftime('%Y-%m-%d')

                ndwi_mean_val = get_ndwi_planet(current_date, next_date, cell_geometry, planet_api_key)
                if ndwi_mean_val is None:
                    continue  # No water pixels or unable to compute NDWI for this day

                update_historical_data(section_name, current_date, ndwi_mean_val)

            # Retrieve and sort the historical data for this grid cell
            history = historical_data.get(section_name, {}).get('history', [])
            if not history:
                continue

            history_sorted = sorted(history, key=lambda x: x['date'])
            latest_entry = history_sorted[-1]
            current_ndwi = latest_entry['ndwi']

            # Set color based on current NDWI and any dramatic drop
            rectangle_color = colormap(current_ndwi)
            if len(history_sorted) >= 2:
                previous_entry = history_sorted[-2]
                previous_ndwi = previous_entry['ndwi']
                if (previous_ndwi - current_ndwi) >= DRAMATIC_DROP_THRESHOLD:
                    rectangle_color = 'red'

            image_url = generate_satellite_image_url(bounds, ee_geometry, google_maps_api_key)

            popup_html = f"""
                <b>{section_name}</b><br>
                Longitude: {bounds[0]} to {bounds[2]}<br>
                Latitude: {bounds[1]} to {bounds[3]}<br>
                NDWI (water pixels only): {current_ndwi:.2f}<br>
                <img src='{image_url}' style='width: 100%; height: 300px;' alt='Satellite Image'><br>
                <button onclick="showHistory('{section_name}')">View Trend</button>
                <canvas id="chart-{section_name}" style="width: 100%; height: 400px; display: none;"></canvas>
            """

            folium.Rectangle(
                bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                color=rectangle_color,
                fill=True,
                fill_opacity=0.2,
                popup=popup_html
            ).add_to(my_map)

    except Exception as e:
        print(f"Error processing {river_name}: {e}")

# Save the updated historical data
save_historical_data(historical_data)

colormap.caption = "NDWI Values: Blue (Clean ~1), Yellow (Dirty ~0), Black (Polluted ~-1)"
colormap.add_to(my_map)
folium.LayerControl().add_to(my_map)
my_map.save("pra_river_monitoring_grid.html")

# Inject global JavaScript and CSS for plotting NDWI trends
with open("pra_river_monitoring_grid.html", "r+") as file:
    content = file.read()
    global_js = """
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    function showHistory(section) {
        const data = JSON.parse(document.getElementById('historical-data').textContent);
        const trend = data[section]['history'].slice().sort((a, b) => new Date(a.date) - new Date(b.date));
        const chartElement = document.getElementById('chart-' + section);
        chartElement.style.display = 'block';
        const ctx = chartElement.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: trend.map(entry => entry.date),
                datasets: [{
                    label: 'NDWI Trend',
                    data: trend.map(entry => entry.ndwi),
                    borderColor: 'blue',
                    fill: false
                }]
            },
            options: {
                scales: {
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'NDWI' } }
                }
            }
        });
    }
    </script>
    """
    custom_css = """
    <style>
    .leaflet-popup-content-wrapper {
        width: 500px !important;
        height: 800px !important;
    }
    .leaflet-popup-content {
        overflow: auto;
    }
    </style>
    """
    historical_data_script = f"<script id='historical-data' type='application/json'>{json.dumps(historical_data)}</script>"
    if global_js not in content:
        content = content.replace("<head>", f"<head>\n{global_js}\n{custom_css}\n{historical_data_script}")
    file.seek(0)
    file.write(content)
    file.truncate()

print("Map saved to 'pra_river_monitoring_grid.html'.")

