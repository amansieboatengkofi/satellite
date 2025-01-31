import requests
import json  # Add this import
import geopandas as gpd
import ee
import folium
from datetime import datetime, timedelta

# Initialize Google Earth Engine
ee.Initialize(project='ee-amansieboatengkofi')


custom_images = [
      {"lat": 5.423506, "lon": -1.621584, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.423506%2CLongitude%3D-1.621584.png?alt=media&token=6507e895-8ac4-4793-a35b-52a3d7fcf249"},
      {"lat": 6.198368, "lon": -1.198020, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.198368%2CLongitude%3D-1.198020.png?alt=media&token=f88d785c-4eae-4dc1-98ff-2906864e4b35"},
      {"lat": 6.184267, "lon": -1.190211, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.184267%2CLongitude%3D-1.190211.png?alt=media&token=60131a2e-b896-46b0-b8fe-0324af2e5ff6"},
      {"lat": 6.185782, "lon": -1.190941, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.185782%2CLongitude%3D-1.190941.png?alt=media&token=d1d690a4-42b5-414c-a4a4-c25b55e13a1c"},
      {"lat": 6.174689, "lon": -1.179459, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.174689%2CLongitude%3D-1.179459.png?alt=media&token=0bcd6cd8-ae8a-4bb8-bff5-af8842bcffb2"},
      {"lat": 6.128309, "lon": -1.199346, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.128309%2CLongitude%3D-1.199346.png?alt=media&token=c65e4cb3-820c-4227-8d9a-a44bfd753865"},
      {"lat": 6.077230, "lon": -1.195935, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.077230%2CLongitude%3D-1.195935.png?alt=media&token=d7b282c1-9a6d-4dd1-b33b-ae21972c586e"},
      {"lat": 6.075950, "lon": -1.204497, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.075950%2CLongitude%3D-1.204497.png?alt=media&token=839f9985-9a49-4f61-a180-dd2162c7714f"},
      {"lat": 6.076035, "lon": -1.204350, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.076035%2CLongitude%3D-1.204350.png?alt=media&token=0deb66e7-253d-4bb6-ac42-473e6ca462f5"},
      {"lat": 6.067500, "lon": -1.211119, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.067500%2CLongitude%3D-1.211119.png?alt=media&token=821535dc-0012-43da-ba1f-f927b91544ef"},
      {"lat": 6.067500, "lon": -1.211139, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.067500%2CLongitude%3D-1.211139.png?alt=media&token=b1f729a3-3247-47bc-a255-73d30bf92e14"},
      {"lat": 6.044967, "lon": -1.222119, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.044967%2CLongitude%3D-1.222119.png?alt=media&token=52b45913-3518-4e17-a573-aafec75c9c1c"},
      {"lat": 6.046333, "lon": -1.219370, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.046333%2CLongitude%3D-1.219370.png?alt=media&token=ad9e5e36-9078-4080-8507-68f46a7107b5"},
      {"lat": 6.044285, "lon": -1.223493, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude6.044285%2CLongitude%3D-1.223493.png?alt=media&token=bc454664-7510-4f4c-87a2-56338ecfdb5a"},
      {"lat": 6.040188, "lon": -1.231016, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.040188%2CLongitude%3D-1.231016.png?alt=media&token=6479ab13-6eb0-4f2b-9eca-8379247a9f82"},
      {"lat": 6.040188, "lon": -1.231055, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.040188%2CLongitude%3D-1.231055.png?alt=media&token=697cc8ca-00a5-455c-9c40-a3f6be3bfc2d"},
      {"lat": 5.881747, "lon": -1.284612, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.881747%2CLongitude%3D-1.284612.png?alt=media&token=6b12e5a0-0c7d-4c85-abe4-ff5cdeb79833"},
      {"lat": 5.884479, "lon": -1.286671, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.884479%2CLongitude%3D-1.286671.png?alt=media&token=201dc998-1aa5-4eb1-b055-6654fe057586"},
      {"lat": 5.909068, "lon": -1.345756, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.909068%2CLongitude%3D-1.345756.png?alt=media&token=d215eb52-5031-4249-92ef-a43e82cb5402"},
      {"lat": 5.910434, "lon": -1.345413, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.910434%2CLongitude%3D-1.345413.png?alt=media&token=5d53b6cf-b669-44c9-8a2f-772c48b9e5a6"},
      {"lat": 5.897457, "lon": -1.453234, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.897457%2CLongitude%3D-1.453234.png?alt=media&token=395fe3a8-812e-4615-b538-ee92e135998c"},
      {"lat": 5.861939, "lon": -1.494268, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.861939%2CLongitude%3D-1.494268.png?alt=media&token=47395fc8-b7d4-49a0-b70f-d00f334d7d72"},
      {"lat": 5.861598, "lon": -1.499079, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.861598%2CLongitude%3D-1.499079.png?alt=media&token=9da31dac-9199-43c8-ac73-b326cdb90cea"},
      {"lat": 5.863305, "lon": -1.500453, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.863305%2CLongitude%3D-1.500453.png?alt=media&token=d882b48c-8412-407d-b159-d248266ae9eb"},
      {"lat": 5.816172, "lon": -1.547505, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.816172%2CLongitude%3D-1.547505.png?alt=media&token=b1bd4bb1-5354-40d0-85a3-dac995f96ddd"},
      {"lat": 5.816514, "lon": -1.548002, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.816514%2CLongitude%3D-1.548002.png?alt=media&token=314385ee-3a49-42c8-9786-f68251dff85d"},
      {"lat": 5.692772, "lon": -1.593698, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.692772%2CLongitude%3D-1.593698.png?alt=media&token=92445f01-b0e6-4dd9-9181-a820a3f0501f"},
      {"lat": 5.691576, "lon": -1.593011, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.691576%2CLongitude%3D-1.593011.png?alt=media&token=7053725c-7500-49a4-8691-54c9879e8340"},
      {"lat": 5.690979, "lon": -1.590262, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.690979%2CLongitude%3D-1.590262.png?alt=media&token=9b172528-3f89-4f71-b013-0aed15da9271"},
      {"lat": 5.690125, "lon": -1.588630, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.690125%2CLongitude%3D-1.588630.png?alt=media&token=5bf3b08e-70f6-4685-a545-8a9a03cc4ee7"},
      {"lat": 5.682438, "lon": -1.582581, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.682438%2CLongitude%3D-1.582581.png?alt=media&token=454fa150-5071-4e1e-b3f4-5b5a50f15543"},
      {"lat": 5.680730, "lon": -1.581979, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.680730%2CLongitude%3D-1.581979.png?alt=media&token=f4a4e6f7-0108-4c9d-bee4-c921f59ac259"},
      {"lat": 5.663349, "lon": -1.547697, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.663349%2CLongitude%3D-1.547697.png?alt=media&token=aa24e89d-ddd7-480e-b38f-d79415222ae4"},
      {"lat": 5.663434, "lon": -1.547740, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.663434%2CLongitude%3D-1.547740.png?alt=media&token=4d97d868-9414-424a-88de-d75da452a9f8"},
      {"lat": 5.436836, "lon": -1.620282, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.436836%2CLongitude%3D-1.620282.png?alt=media&token=3e00e50a-96f7-4845-b945-065e69b9d5d6"},
      {"lat": 5.436921, "lon": -1.619423, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.436921%2CLongitude%3D-1.619423.png?alt=media&token=f92c98b5-f7a1-40ab-9e63-5e8c70516bc7"},
      {"lat": 5.436750, "lon": -1.618135, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.436750%2CLongitude%3D-1.618135.png?alt=media&token=a8bcb5f6-920b-4a80-b3e0-88021a86bb4e"},
      {"lat": 5.274384, "lon": -1.591764, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.274384%2CLongitude%3D-1.591764.png?alt=media&token=a19258fa-5b11-49d5-a38a-b075b6c3c191"},
      {"lat": 5.155658, "lon": -1.648020, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.155658%2CLongitude%3D-1.648020.png?alt=media&token=de0d97b4-50f7-402f-ab59-efb2eeb47189"},
   
]


# Function to fetch river geometry using Overpass API and relation ID
def fetch_river_by_relation_id(relation_id):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    relation({relation_id});
    (._;>;);
    out geom;
    """
    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise ValueError(f"Error fetching data from Overpass API: {response.status_code}")
    data = response.json()

    features = []
    for element in data['elements']:
        if element['type'] == 'way' and 'geometry' in element:
            coords = [(pt['lon'], pt['lat']) for pt in element['geometry']]
            features.append({
                "type": "Feature",
                "properties": {"id": element['id']},
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })
    if not features:
        raise ValueError(f"No geometry found for relation ID {relation_id}")
    gdf = gpd.GeoDataFrame.from_features(features)
    return gdf

def gdf_to_ee_geometry(gdf):
    geom = gdf.geometry.unary_union
    return ee.Geometry(geom.__geo_interface__)


def find_custom_image(lat, lon, threshold=0.001):  # Approx 100m in lat/lon
    for entry in custom_images:
        if abs(entry["lat"] - lat) <= threshold and abs(entry["lon"] - lon) <= threshold:
            return entry["url"]
    return None


# NDWI calculation
def calculate_ndwi_sentinel(image):
    green = image.select('B3')
    nir = image.select('B8')
    ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
    return image.addBands(ndwi)

# Relation IDs for rivers
relation_ids = {
    'Volta River': 1205528,
    'Pra River': 5250354,
    'Ankobra River': 3328713,
}

# Dynamic dates
end_date = datetime.utcnow()-  timedelta(days=30)
start_date = end_date - timedelta(days=15)

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

print(f"Date range: {start_date_str} to {end_date_str}")

# Visualization parameters with forest green for river borders
ndwi_vis_params = {
    'min': -1,
    'max': 1,
    'palette': ['#021702', '#946c10', '#106987']  # Forest Green for forest, Light Beige for dirty water, Blue for clean water
}
buffer_distance = 1000  # 1 km
border_color = 'black'  # Black dashed border

# Google Maps API key (replace with your API key)
google_maps_api_key = "AIzaSyBaraoG9hMuLfTdTqMBvwHcWzjvDeDBNYo"

# Generate individual maps for each river
for river_name, relation_id in relation_ids.items():
    print(f"Processing {river_name}...")
    gdf = fetch_river_by_relation_id(relation_id)

    # Convert river geometry to Earth Engine geometry and buffer it
    ee_geometry = gdf_to_ee_geometry(gdf)
    buffer_1km = ee_geometry.buffer(buffer_distance)

    # Process Sentinel-2 NDWI data
    sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterDate(start_date_str, end_date_str) \
        .filterBounds(buffer_1km) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .map(calculate_ndwi_sentinel)

    sentinel_median = sentinel.median().select('NDWI').clip(buffer_1km)

    # Create NDWI masks
    dirty_water_mask = sentinel_median.gt(-0.3).And(sentinel_median.lte(0.1))
    dirty_water_vector = dirty_water_mask.updateMask(dirty_water_mask).reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.countEvery(),
        scale=30,
        maxPixels=1e9
    )

    # Calculate a smaller section of the river for initial view (1/6th of the river bounds)
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    min_lon, min_lat, max_lon, max_lat = bounds
    section_bounds = [
        [min_lat, min_lon],
        [min_lat + (max_lat - min_lat) / 6, min_lon + (max_lon - min_lon) / 6]
    ]
    center_lat = min_lat + (max_lat - min_lat) / 12  # Center of the sixth section
    center_lon = min_lon + (max_lon - min_lon) / 12

    # Create a map centered on the one-sixth section
    river_map = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    river_map.fit_bounds(section_bounds)  # Fit map to the smaller section

    # Add NDWI visualization as a toggleable layer
    ndwi_map_id = sentinel_median.getMapId(ndwi_vis_params)
    folium.TileLayer(
        tiles=ndwi_map_id['tile_fetcher'].url_format,
        name=f"{river_name} - NDWI",
        overlay=True,
        attr="Google Earth Engine"
    ).add_to(river_map)

    # Add dirty water visualization
    folium.GeoJson(
        data=dirty_water_vector.getInfo(),
        name=f"(Yellow) Galamsey spots on - {river_name}",
        style_function=lambda x: {
            'fillColor': 'yellow',
            'color': 'yellow',
            'weight': 2,
            'fillOpacity': 0.5
        }
    ).add_to(river_map)

    # Add the 1 km buffer zone with dashed borders
    folium.GeoJson(
        data=buffer_1km.getInfo(),
        name=f"{river_name} Buffer (1km)",
        style_function=lambda x: {
            'color': border_color,
            'weight': 1,
            'dashArray': '5, 5',  # Dashed line
            'fillOpacity': 0
        }
    ).add_to(river_map)

    # Add a click event to fetch and display a zoomable Google Maps Static Image in a bigger popup
    click_js = f"""
    document.addEventListener('DOMContentLoaded', function() {{
        var map = window.{river_map.get_name()};
        if (map) {{
            map.on('click', function(e) {{
                var lat = e.latlng.lat.toFixed(6);
                var lon = e.latlng.lng.toFixed(6);

                // Check if there's a custom image for this location
                var customImages = {json.dumps(custom_images)};
                var customImageUrl = null;
                for (var i = 0; i < customImages.length; i++) {{
                    var entry = customImages[i];
                    if (Math.abs(entry.lat - lat) <= 0.001 && Math.abs(entry.lon - lon) <= 0.001) {{
                        customImageUrl = entry.url;
                        break;
                    }}
                }}

                var imageUrl;
                var googleMapsLink = `https://www.google.com/maps/@${{lat}},${{lon}},16z`;

                if (customImageUrl) {{
                    imageUrl = customImageUrl;  // Use custom image
                }} else {{
                    imageUrl = `https://maps.googleapis.com/maps/api/staticmap?center=${{lat}},${{lon}}&zoom=17&size=2400x1800&maptype=satellite&key={google_maps_api_key}`;
                }}

                const popupContent = `
                    <b>Coordinates:</b><br>
                    Latitude: ${{lat}}, Longitude: ${{lon}}<br><br>
                    <div style="width:308px; overflow:auto;">
                        <img src="${{imageUrl}}" alt="Satellite Image" style="width:100%;height:auto; cursor: zoom-in;" 
                            onclick="this.style.transform='scale(2)'; this.style.cursor='zoom-out';" 
                            ondblclick="this.style.transform='scale(1)'; this.style.cursor='zoom-in';">
                    </div>
                    <br>
                    <a href="${{googleMapsLink}}" target="_blank" style="text-decoration: none; color: white; 
                    background-color: #007bff; padding: 8px 12px; border-radius: 5px;">
                    Go to Google Maps
                    </a>
                `;

                const popup = L.popup({{ maxWidth: 400 }})
                    .setLatLng(e.latlng)
                    .setContent(popupContent)
                    .openOn(map);
            }});
        }}
    }});
    """


    river_map.get_root().script.add_child(folium.Element(click_js))

    # Add layer control
    folium.LayerControl().add_to(river_map)

    # Save the map as an HTML file
    filename = f"{river_name.replace(' ', '_').lower()}_monitoring.html"
    river_map.save(filename)
    print(f"Map for {river_name} saved as {filename}")
