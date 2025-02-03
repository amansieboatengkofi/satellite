import requests
import json  # Add this import
import geopandas as gpd
import ee
import folium
from datetime import datetime, timedelta
from shapely.geometry import Point

# Initialize Google Earth Engine
ee.Initialize(project='ee-amansieboatengkofi')


custom_images = [
      {"lat": 5.423506, "lon": -1.621584, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.423506%2CLongitude%3D-1.621584.png?alt=media&token=0a4043a1-08c0-4217-a093-521ccd667921"},
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
      
      {"lat": 5.330704, "lon": -1.620727, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.330704%2CLongitude%3D-1.620727.png?alt=media&token=7ca41a69-fa3c-47a2-8d01-c98255f8c2ec"},
      {"lat": 5.388045, "lon": -1.638055, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.388045%2CLongitude%3D-1.638055.png?alt=media&token=e6dc7f6e-88ee-46b6-9eb7-e1bc3ec92a25"},
      {"lat": 5.384712, "lon": -1.639096, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.384712%2CLongitude%3D-1.639096.png?alt=media&token=925cab50-3e70-449d-a98f-73e3bbd0878a"},
 
      {"lat": 5.662238, "lon": -1.549426, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.662238%2CLongitude%3D-1.549426.png?alt=media&token=23b38887-3b87-43a7-b662-b0e5e69b206d"},
      {"lat": 5.661768, "lon": -1.548555, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.662238%2CLongitude%3D-1.549426.png?alt=media&token=23b38887-3b87-43a7-b662-b0e5e69b206d"},

      {"lat": 5.914873, "lon": -1.348997, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.914873%2CLongitude%3D-1.348997.png?alt=media&token=82abab42-476b-42fb-838d-ad443bc34b90"},

      {"lat": 5.882985, "lon": -1.287235, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.884479%2CLongitude%3D-1.286671.png?alt=media&token=201dc998-1aa5-4eb1-b055-6654fe057586"},

    
      {"lat": 5.884992, "lon": -1.285302, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D5.884992%2CLongitude%3D-1.285302.png?alt=media&token=4ad4935e-4980-4d65-9a82-22ad23f2647b"},

      {"lat": 6.048040, "lon": -1.214126, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.048040%2CLongitude%3D-1.214126.png?alt=media&token=87bf0469-16eb-40d2-ac43-ba3569fd5557"},

      {"lat": 6.073133, "lon": -1.209143, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.073133%2CLongitude%3D-1.209143.png?alt=media&token=3a399079-95eb-4cbc-96f6-617dbd0ad1a5"},

      {"lat": 6.072771, "lon": -1.206597, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.072771%2CLongitude%3D-1.206597.png?alt=media&token=551ff785-6356-4fe9-ae2a-32cf95cd10d6"},

      {"lat": 6.074350, "lon": -1.206318, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.072771%2CLongitude%3D-1.206597.png?alt=media&token=551ff785-6356-4fe9-ae2a-32cf95cd10d6"},

      {"lat": 6.077294, "lon": -1.204376, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.075950%2CLongitude%3D-1.204497.png?alt=media&token=839f9985-9a49-4f61-a180-dd2162c7714f"},

             
      {"lat": 6.077443, "lon": -1.197375, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.077230%2CLongitude%3D-1.195935.png?alt=media&token=d7b282c1-9a6d-4dd1-b33b-ae21972c586e"},
 

      {"lat": 6.172385, "lon": -1.180163, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.174689%2CLongitude%3D-1.179459.png?alt=media&token=0bcd6cd8-ae8a-4bb8-bff5-af8842bcffb2"},
 
      {"lat": 6.185953, "lon": -1.192568, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.185953%2CLongitude%3D-1.192568.png?alt=media&token=7e95bebc-54a0-4f10-b9a5-44c7faa74638"},
 
      {"lat": 6.187574, "lon": -1.190936, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.187574%2CLongitude%3D-1.190936.png?alt=media&token=8f714a2c-fa2f-40aa-aff5-8561fcbc9305"},
 
      {"lat": 6.188811, "lon": -1.187586, "url": "https://firebasestorage.googleapis.com/v0/b/borgapiano.appspot.com/o/Latitude%3D6.188811%2CLongitude%3D-1.187586.png?alt=media&token=9d3cc3a1-d4e0-4e37-87ac-d132dafa7bc2"},
 
     
      ]


# List of exclusion zones where no yellow spots should be marked (lat, lon)
exclusion_zones = [
    (5.116036, -1.620820, 500), #long, lat, radius within which to exclude galamsey spots for long lat
    (5.121464, -1.612307, 500),
    (5.117275, -1.621335, 100),
    (5.117788, -1.620903, 100),
    (5.122832, -1.612994, 100),

    (5.012287, -1.630715, 1000),
    (5.028361, -1.612351, 1000),
    (5.032550, -1.628607, 100),
    (5.030691, -1.610348, 100),
    (5.016904, -1.620952, 100),
    (5.049736, -1.610247, 100),
    (5.052301, -1.604034, 100),
    (5.050804, -1.624125, 100),
    (5.031311, -1.628374, 100),
    (5.036911, -1.631595, 100),
    (5.117361, -1.613682, 100),
    (5.120182, -1.615915, 100),
    (5.138391, -1.658422, 500),
    (5.142579, -1.657391, 150),
    (5.173610, -1.607081, 100),
    (5.187372, -1.567726, 100),
    (5.194381, -1.569788, 150),
    (5.198655, -1.569273, 100),
    (5.242589, -1.607928, 100),
    (5.195407, -1.570316, 150),
    (5.187885, -1.568255, 100),
    (5.241307, -1.606219, 100),
    (5.244128, -1.608453, 100),
    (5.246521, -1.610343, 100),
    (5.260965, -1.602017, 100),
    (5.272845, -1.582947, 100),
    (5.288486, -1.592055, 100),
    (5.320022, -1.594301, 100),
    (5.322158, -1.597156, 100),
    (5.162561, -1.629449, 100),
    (5.179273, -1.606404, 100),
    (5.260111, -1.598582, 100),
    (5.387532, -1.640470, 100),
    (5.405391, -1.635835, 150),
    (5.428953, -1.631167, 200),
    (5.463472, -1.613592, 100),
    (5.532611, -1.613938, 130),
    (5.539574, -1.607669, 100),
    (5.612356, -1.550349, 700),
    (5.603045, -1.549662, 700),
    (5.618079, -1.535583, 100),
    (5.593435, -1.547662, 100),
    (5.598389, -1.544237, 100),
    (5.607444, -1.541832, 300),
    (5.617182, -1.533414, 300),
    (5.610006, -1.541476, 200),
    (5.616327, -1.530824, 200),
    (5.645924, -1.533783, 100),
    (5.668559, -1.542542, 100),
    (5.689142, -1.578800, 100),
    (5.703619, -1.603223, 400),
    (5.739488, -1.605107, 100),
    (5.808573, -1.582500, 250),
    (5.866891, -1.548544, 200),
    (5.868172, -1.546569, 100),
    (5.870733, -1.548888, 150),
    (5.868684, -1.491628, 100),
    (5.864500, -1.484756, 100),
    (5.910861, -1.467781, 200),
    (5.893615, -1.465974, 150),
    (5.927765, -1.423202, 200),
    (5.899420, -1.425178, 300),
    (5.928191, -1.366326, 500),
    (5.937924, -1.364780, 500),
    (5.925289, -1.360141, 200),
    (5.904031, -1.304488, 150),
    (5.882260, -1.296717, 100),
    (5.889132, -1.254014, 100),
    (5.948680, -1.213421, 150),
    (6.137056, -1.207250, 300),
    (6.135520, -1.205747, 100),
    (6.169228, -1.190377, 200),
    
    (5.004933, -1.625462, 100),
    (5.004933, -1.632586, 100),
    (5.053156, -1.604176, 100),
    (5.071452, -1.621599, 100),

    (5.074786, -1.623573, 100),
    (5.111718, -1.623917, 100),
    (5.128218, -1.610184, 150),
    (5.124114, -1.624346, 100),
    (5.125482, -1.623917, 100),
    (5.130098, -1.653357, 100),
    (5.137194, -1.650181, 100),
    (5.142579, -1.661425, 100),
    (5.142665, -1.655889, 100),
    (5.143648, -1.655803, 100),
    (5.047000, -1.632997, 100)
    






    







    # Add more known locations where no galamsey operations occur
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

# Function to filter out points within 50 meters of exclusion zones
def is_within_exclusion_zone(lat, lon ):
    for ex_lat, ex_lon, radius in exclusion_zones:
        point1 = Point(lon, lat)
        point2 = Point(ex_lon, ex_lat)
        distance = point1.distance(point2) * 111139  # Approximate conversion to meters
        if distance <= radius:
            # print(f"Point ({lat}, {lon}) is within exclusion zone ({ex_lat}, {ex_lon}) with radius {radius} meters.")
            return True
    return False

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

# # Generate individual maps for each river
# for river_name, relation_id in relation_ids.items():
#     print(f"Processing {river_name}...")
#     gdf = fetch_river_by_relation_id(relation_id)

#     # Convert river geometry to Earth Engine geometry and buffer it
#     ee_geometry = gdf_to_ee_geometry(gdf)
#     buffer_1km = ee_geometry.buffer(buffer_distance)

#     # Process Sentinel-2 NDWI data
#     sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
#         .filterDate(start_date_str, end_date_str) \
#         .filterBounds(buffer_1km) \
#         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
#         .map(calculate_ndwi_sentinel)

#     sentinel_median = sentinel.median().select('NDWI').clip(buffer_1km)

#     # Create NDWI masks
#     dirty_water_mask = sentinel_median.gt(-0.3).And(sentinel_median.lte(0.1))
#     dirty_water_vector = dirty_water_mask.updateMask(dirty_water_mask).reduceToVectors(
#         geometryType='polygon',
#         reducer=ee.Reducer.countEvery(),
#         scale=30,
#         maxPixels=1e9
#     )

#     # Calculate a smaller section of the river for initial view (1/6th of the river bounds)
#     bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
#     min_lon, min_lat, max_lon, max_lat = bounds
#     section_bounds = [
#         [min_lat, min_lon],
#         [min_lat + (max_lat - min_lat) / 6, min_lon + (max_lon - min_lon) / 6]
#     ]
#     center_lat = min_lat + (max_lat - min_lat) / 12  # Center of the sixth section
#     center_lon = min_lon + (max_lon - min_lon) / 12

#     # Create a map centered on the one-sixth section
#     river_map = folium.Map(location=[center_lat, center_lon], zoom_start=18)
#     river_map.fit_bounds(section_bounds)  # Fit map to the smaller section

#     # Add NDWI visualization as a toggleable layer
#     ndwi_map_id = sentinel_median.getMapId(ndwi_vis_params)
#     folium.TileLayer(
#         tiles=ndwi_map_id['tile_fetcher'].url_format,
#         name=f"{river_name} - NDWI",
#         overlay=True,
#         attr="Google Earth Engine"
#     ).add_to(river_map)

#     # Add dirty water visualization
#     folium.GeoJson(
#         data=dirty_water_vector.getInfo(),
#         name=f"(Yellow) Galamsey spots on - {river_name}",
#         style_function=lambda x: {
#             'fillColor': 'yellow',
#             'color': 'yellow',
#             'weight': 2,
#             'fillOpacity': 0.5
#         }
#     ).add_to(river_map)

#     # Add the 1 km buffer zone with dashed borders
#     folium.GeoJson(
#         data=buffer_1km.getInfo(),
#         name=f"{river_name} Buffer (1km)",
#         style_function=lambda x: {
#             'color': border_color,
#             'weight': 1,
#             'dashArray': '5, 5',  # Dashed line
#             'fillOpacity': 0
#         }
#     ).add_to(river_map)


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

    # Convert Earth Engine feature collection to GeoJSON
    dirty_water_json = dirty_water_vector.getInfo()
    filtered_features = []

    for feature in dirty_water_json['features']:
        coordinates = feature['geometry']['coordinates'][0]  # Assuming polygon structure
        centroid_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        centroid_lon = sum(coord[0] for coord in coordinates) / len(coordinates)

        if not is_within_exclusion_zone(centroid_lat, centroid_lon):
            filtered_features.append(feature)

    # Update the dirty water vector with filtered features
    dirty_water_json['features'] = filtered_features

    # # Calculate center for map
    # bounds = gdf.total_bounds
    # min_lon, min_lat, max_lon, max_lat = bounds
    # center_lat = (min_lat + max_lat) / 2
    # center_lon = (min_lon + max_lon) / 2

    # # Create folium map
    # river_map = folium.Map(location=[center_lat, center_lon], zoom_start=14)


    # # Calculate a smaller section of the river for initial view (1/6th of the river bounds)
    #-----------------
    # bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    # min_lon, min_lat, max_lon, max_lat = bounds
    # section_bounds = [
    #     [min_lat, min_lon],
    #     [min_lat + (max_lat - min_lat) / 6, min_lon + (max_lon - min_lon) / 6]
    # ]
    # center_lat = min_lat + (max_lat - min_lat) / 12  # Center of the sixth section
    # center_lon = min_lon + (max_lon - min_lon) / 12

    # # Create a map centered on the one-sixth section
    # river_map = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    # river_map.fit_bounds(section_bounds)  # Fit map to the smaller section
    #------------------
    # Calculate the total bounds of the river geometry [minx, miny, maxx, maxy]
    bounds = gdf.total_bounds
    min_lon, min_lat, max_lon, max_lat = bounds

    # Calculate the middle sixth of the river’s bounding box.
    # This picks the vertical and horizontal section from 2/6 to 3/6 of the total range.
    section_bounds = [
        [min_lat + 3 * (max_lat - min_lat) / 7, min_lon + (max_lon - min_lon) / 12 ], #Aman modifying these values for pra river. see above sectional values block for default lat long values
        [min_lat + 4 * (max_lat - min_lat) / 7, min_lon +   (max_lon - min_lon) / 5] #Aman modifying these values for pra river. see above sectional values block for default lat long values
    ]

    # Calculate the center of this section.
    center_lat = min_lat + 3.5 * (max_lat - min_lat) / 7
    center_lon = min_lon + 3.5 * (max_lon - min_lon) / 7

    # Shift the center to the left by subtracting, e.g., 10% of the total width.
    # center_lon -= (max_lon - min_lon) * 0.1
    center_lon = min_lon #Aman modifying these values for pra river. see above sectional values block for default lat long values
    center_lon = min_lon +  (max_lon - min_lon) / 12


    # Create a map centered on the adjusted center and fit the section bounds.
    river_map = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    river_map.fit_bounds(section_bounds)

    # Add NDWI visualization
    ndwi_map_id = sentinel_median.getMapId(ndwi_vis_params)
    folium.TileLayer(
        tiles=ndwi_map_id['tile_fetcher'].url_format,
        name=f"{river_name} - NDWI",
        overlay=True,
        attr="Google Earth Engine"
    ).add_to(river_map)

    # Add filtered galamsey spots
    folium.GeoJson(
        data=dirty_water_json,
        name=f"(Yellow) Galamsey spots - {river_name}",
        style_function=lambda x: {
            'fillColor': 'yellow',
            'color': 'yellow',
            'weight': 2,
            'fillOpacity': 0.5
        }
    ).add_to(river_map)

    # # Save the map
    # filename = f"{river_name.replace(' ', '_').lower()}_monitoring.html"
    # river_map.save(filename)
    # print(f"Map for {river_name} saved as {filename}")

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
                    <div style="width:462px; overflow:auto;">
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

                const popup = L.popup({{ maxWidth: 600 }})
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
