# pollution tracking for pra
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
HISTORICAL_DATA_FILE = "pra_ndwi_historical_data.json"
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

def generate_clipped_grid(geometry, grid_size=0.005):
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
    """Generates a Google Maps Static API URL for a high-resolution satellite image."""
    bbox = ee.Geometry.Rectangle(bounds)
    river_section = river_geometry.intersection(bbox)

    try:
        coordinates = river_section.coordinates().getInfo()
        if coordinates and isinstance(coordinates[0], list):
            lon, lat = coordinates[0][0][0], coordinates[0][1][1]
            print(f"Using river intersection point for center: lat={lat}, lon={lon}")
        else:
            raise ValueError("No valid river coordinates found.")
    except Exception as e:
        print(f"Warning: Using bounding box center due to error: {e}")
        lon = (bounds[0] + bounds[2]) / 2
        lat = (bounds[1] + bounds[3]) / 2
        print(f"Using bounding box center as fallback: lat={lat}, lon={lon}")

    # Construct a valid Google Maps Static API URL
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=17&size=2400x1800&maptype=satellite&key={api_key}"

# Rivers to process
relation_ids = {
    'Pra River': 5250354,
}

# Fetch Pra River geometry for map centering
pra_geometry = fetch_river_by_relation_id(relation_ids['Pra River'])
pra_coordinates = gdf_to_ee_geometry(pra_geometry).coordinates().getInfo()
pra_center = pra_coordinates[len(pra_coordinates) // 2]  # Approximate center of the river

# Map initialization, centered and zoomed into the Pra River
my_map = folium.Map(location=[pra_center[1], pra_center[0]], zoom_start=10)

# Dynamic date range
end_date = datetime.now()
start_date = end_date - timedelta(days=10)
start_date, end_date = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

grid_size = 0.04  # 5 km grid size
alerts = []

# NDWI Visualization Parameters
ndwi_vis_params = {'min': -1, 'max': 1, 'palette': ['red', 'yellow', 'green']}
colormap = LinearColormap(['red', 'yellow', 'green'], vmin=-1, vmax=1)

google_maps_api_key = "AIzaSyBaraoG9hMuLfTdTqMBvwHcWzjvDeDBNYo"

for river_name, relation_id in relation_ids.items():
    print(f"Processing {river_name}...")
    try:
        river_lines = fetch_river_by_relation_id(relation_id)
        ee_geometry = gdf_to_ee_geometry(river_lines).buffer(1)

        # Generate clipped grid
        grid_cells = generate_clipped_grid(ee_geometry, grid_size)

        # Create a FeatureCollection from the grid cells
        grid_features = [ee.Feature(cell_data["geometry"], {
            'bounds': cell_data["bounds"],
            'section_name': f"{river_name} - Grid {idx+1}"
        }) for idx, cell_data in enumerate(grid_cells)]
        grid_fc = ee.FeatureCollection(grid_features)

        # Prepare the Sentinel-2 NDWI image
        sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterDate(start_date, end_date) \
            .filterBounds(ee_geometry) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .map(calculate_ndwi_sentinel)

        # Print acquisition dates of the images
        image_dates = sentinel.aggregate_array('system:time_start').getInfo()
        if image_dates:
            print(f"Dates of images for {river_name}:")
            for date_ms in image_dates:
                image_date = datetime.utcfromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                print(f" - {image_date}")
        else:
            print(f"No valid images found for {river_name} in the specified time range.")

        # Check if the collection is empty
        if sentinel.size().getInfo() == 0:
            print(f"No valid Sentinel-2 images found for {river_name} in the specified time range.")
            continue

        ndwi_image = sentinel.median().select('NDWI')

        def compute_mean_ndwi(feature):
            ndwi_mean = ndwi_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=feature.geometry(),
                scale=30
            )
            return feature.set({'mean_ndwi': ndwi_mean.get('NDWI')})

        mean_ndwi_fc = grid_fc.map(compute_mean_ndwi)
        mean_ndwi_list = mean_ndwi_fc.getInfo()['features']

        for feature in mean_ndwi_list:
            properties = feature['properties']
            section_name = properties['section_name']
            mean_ndwi = properties.get('mean_ndwi', None)
            bounds = properties['bounds']

            if mean_ndwi is not None:
                prev_data = historical_data.get(section_name, {}).get('history', [])
                current_entry = {'date': datetime.now().strftime('%Y-%m-%d'), 'ndwi': mean_ndwi}
                prev_data.append(current_entry)
                historical_data[section_name] = {'history': prev_data}

                # Generate the satellite image URL using a point on the river
                image_url = generate_satellite_image_url(bounds, ee_geometry, google_maps_api_key)

                popup_html = f"""
                <b>{section_name}</b><br>
                NDWI: {mean_ndwi:.2f}<br>
                <img src="{image_url}" style="width: 100%; height: 300px;" alt="Satellite Image of River Section"><br>
                <button onclick="showHistory('{section_name}')">View Trend</button>
                <canvas id="chart-{section_name}" style="width: 100%; height: 400px; display: none;"></canvas>
                """

                folium.Rectangle(
                    bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                    color=colormap(mean_ndwi),
                    fill=True,
                    fill_opacity=0.01, #Aman changing opacity
                    popup=popup_html
                ).add_to(my_map)

    except Exception as e:
        print(f"Error processing {river_name}: {e}")

save_historical_data(historical_data)
colormap.caption = "NDWI Values (Pollution Levels)"
colormap.add_to(my_map)
folium.LayerControl().add_to(my_map)
my_map.save("pra_river_monitoring_grid.html")

# Inject global JavaScript and CSS for popup size into the saved HTML
with open("pra_river_monitoring_grid.html", "r+") as file:
    content = file.read()
    global_js = """
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
    <script>
    function showHistory(section) {
        const data = JSON.parse(document.getElementById('historical-data').textContent);
        const trend = data[section]['history'];
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

print("\n".join(alerts) if alerts else "No significant pollution changes detected.")
print("Map saved to 'pra_river_monitoring_grid.html'.")
