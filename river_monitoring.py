import requests
import geopandas as gpd
import ee
import folium
from datetime import datetime, timedelta

# Initialize Google Earth Engine
ee.Initialize(project='ee-amansieboatengkofi')

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
end_date = datetime.utcnow()-  timedelta(days=1)
start_date = end_date - timedelta(days=5)

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
    dirty_water_mask = sentinel_median.gt(-0.2).And(sentinel_median.lte(0.1))
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

                // Construct Google Maps Static API URL
                const imageUrl = `https://maps.googleapis.com/maps/api/staticmap?center=${{lat}},${{lon}}&zoom=17&size=2400x1800&maptype=satellite&key={google_maps_api_key}`;
                const googleMapsLink = `https://www.google.com/maps/@${{lat}},${{lon}},16z`;

                // Create popup content with zoomable satellite image, description, and Google Maps link
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

                // Display popup with zoomable content
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
