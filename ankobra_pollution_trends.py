import requests
import json
import ee
import folium
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
from branca.colormap import LinearColormap
from datetime import datetime, timedelta

# Initialize Google Earth Engine
ee.Initialize(project='ee-amansieboatengkofi')

# Historical NDWI data storage
HISTORICAL_DATA_FILE = "ankobra_ndwi_historical_data.json"
try:
    with open(HISTORICAL_DATA_FILE, 'r') as file:
        historical_data = json.load(file)
except FileNotFoundError:
    historical_data = {}

def save_historical_data(data):
    with open(HISTORICAL_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Fetch river geometry
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

def calculate_ndwi_sentinel(image):
    green = image.select('B3')  # Green band
    nir = image.select('B8')    # Near-Infrared band
    ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
    water_mask = ndwi.gt(-0.3)  # Include water even if polluted
    return image.addBands(ndwi.updateMask(water_mask))

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

    # Filter history to keep only the last 60 days
    section_history = [entry for entry in section_history if (datetime.now() - datetime.strptime(entry['date'], '%Y-%m-%d')).days <= 60]

    # Add new entry for the current date if not already present
    if not any(entry['date'] == date for entry in section_history):
        section_history.append({'date': date, 'ndwi': mean_ndwi})

    historical_data[section_name] = {'history': section_history}

# Rivers to process
relation_ids = {
    'Ankobra River': 3328713,
}

# Fetch Ankobra River geometry for map centering
ankobra_geometry = fetch_river_by_relation_id(relation_ids['Ankobra River'])
ankobra_coordinates = gdf_to_ee_geometry(ankobra_geometry).coordinates().getInfo()
ankobra_center = ankobra_coordinates[len(ankobra_coordinates) // 2]  # Approximate center of the river

# Map initialization, centered and zoomed into the ankobra River
my_map = folium.Map(location=[ankobra_center[1], ankobra_center[0]], zoom_start=10)

# Dynamic date range
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
start_date, end_date = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

grid_size = 0.04  # 5 km grid size

# NDWI Visualization Parameters
ndwi_vis_params = {'min': -1, 'max': 1, 'palette': ['red', 'yellow', 'green']}
colormap = LinearColormap(['red', 'yellow', 'green'], vmin=-1, vmax=1)

api_key = "AIzaSyBaraoG9hMuLfTdTqMBvwHcWzjvDeDBNYo"

for river_name, relation_id in relation_ids.items():
    print(f"Processing {river_name}...")
    try:
        river_lines = fetch_river_by_relation_id(relation_id)
        ee_geometry = gdf_to_ee_geometry(river_lines).buffer(1)

        # Generate clipped grid
        grid_cells = generate_clipped_grid(ee_geometry, grid_size)

        for day_offset in range(60):
            current_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            next_date = (datetime.now() - timedelta(days=day_offset - 1)).strftime('%Y-%m-%d')

            for idx, cell in enumerate(grid_cells):
                cell_geometry = cell["geometry"]
                bounds = cell["bounds"]
                section_name = f"{river_name} - Grid {idx + 1}"

                # Prepare the Sentinel-2 NDWI image for the specific day
                sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                    .filterDate(current_date, next_date) \
                    .filterBounds(cell_geometry) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .map(calculate_ndwi_sentinel)

                if sentinel.size().getInfo() == 0:
                    continue  # Skip if no images are available for the day

                ndwi_image = sentinel.median().select('NDWI')

                ndwi_mean = ndwi_image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=cell_geometry,
                    scale=30
                ).get('NDWI')

                if ndwi_mean is not None:
                    ndwi_mean = ndwi_mean.getInfo()  # Resolve the ComputedObject

                if ndwi_mean is None:
                    continue  # Skip this grid cell if no NDWI value is available

                ndwi_mean = float(ndwi_mean)
                update_historical_data(section_name, current_date, ndwi_mean)

                image_url = generate_satellite_image_url(bounds, ee_geometry, api_key)

                popup_html = f"""
                <b>{section_name}</b><br>
                Longitude: {bounds[0]} to {bounds[2]}<br>
                Latitude: {bounds[1]} to {bounds[3]}<br>
                <img src='{image_url}' style='width: 100%; height: 300px;' alt='Satellite Image'><br>
                <button onclick=\"showHistory('{section_name}')\">View Trend</button>
                <canvas id=\"chart-{section_name}\" style=\"width: 100%; height: 400px; display: none;\"></canvas>
                """

                folium.Rectangle(
                    bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                    color=colormap(ndwi_mean),
                    fill=True,
                    fill_opacity=0.01,
                    popup=popup_html
                ).add_to(my_map)

    except Exception as e:
        print(f"Error processing {river_name}: {e}")

save_historical_data(historical_data)
colormap.caption = "NDWI Values (Pollution Levels)"
colormap.add_to(my_map)
folium.LayerControl().add_to(my_map)
my_map.save("ankobra_river_monitoring_grid.html")

# Inject global JavaScript and CSS for plotting trends
with open("ankobra_river_monitoring_grid.html", "r+") as file:
    content = file.read()
    global_js = """
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
    <script>
    function showHistory(section) {
        const data = JSON.parse(document.getElementById('historical-data').textContent);
        const trend = data[section]['history'].slice().reverse(); // Reverse trend data for correct order;
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

print("Map saved to 'ankobra_river_monitoring_grid.html'.")


