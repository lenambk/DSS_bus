import geopandas as gpd
import json
import os
from shapely.geometry import Point

def get_oneway_id(file_path):
    "hàm xử lý data đường 1 chiều từ file .geojson"
    oneway_id = []
    bus_name = []
    with open(file_path, 'r', encoding='utf-8' ) as file:
        f = file.read()
        data_geojson = json.loads(f)

        for way in data_geojson['features']:
            if 'properties' in way and 'oneway' in way['properties'] and way['properties']['oneway'] == 'yes':
                oneway_id.append(way['properties']['@id'])
            if 'properties' in way and 'name' in way['properties']:
                bus_name.append(way['properties']['name'])
    return oneway_id, bus_name

# file = 'bus_stop.geojson'
file = 'hoguom.geojson'
file_path = os.path.join(os.getcwd(), '..', 'preprocess_data', 'data', file)

gdf = gpd.read_file(file_path)
oneway_id, bus_id = get_oneway_id(file_path)

file_bus = 'bus.geojson'
file_bus_path = os.path.join(os.getcwd(), '..', 'preprocess_data', 'data', file_bus)

gdf_bus = gpd.read_file(file_bus_path)

# tìm điểm xe buýt gần với điểm đã chọn nhất
def get_nearest_bus(point, type):
    gdf_bus['distance'] = gdf_bus['geometry'].distance(point)
    nearest_bus = gdf_bus.loc[gdf_bus['distance'].idxmin()]
    return nearest_bus['geometry']


# Trả ra những điểm H, A, B nằm trên đường gần bus_stop nhất, type (start or target)
def get_nearest_point(point, type):
    "hàm lấy ra điểm xe buýt"
    # Trên đường MN
    # H là chân đường vuông góc từ point tới MN
    # A thuộc các node (được lưu trong data) gần H nhất
    # A, B đối xứng qua H
    gdf['distance'] = gdf['geometry'].distance(point)
    nearest_road = gdf.loc[gdf['distance'].idxmin()]
    print('name:', nearest_road)
    line = nearest_road['geometry']
    try:
        point_H = line.interpolate(line.project(point))
    except Exception as err:
        print('err:', err)
    way_id = nearest_road['id']
    name = nearest_road['name']

    min_d1 = 10000000
    point_A = point_H

    coords = line.coords
    i = 0
    # lấy điểm A gần point nhất
    for p in coords:
        d = point.distance(Point(p))
        if min_d1 > d:
            k_a = i
            point_A = Point(p)
            min_d1 = d
        else:
            break
        i += 1

    vector_HA = (point_A.x - point_H.x, point_A.y - point_H.y)
    if k_a < len(coords) -1 :
        k_b = k_a + 1
        point_B = Point(coords[k_b])
        vector_HB = (point_B.x - point_H.x, point_B.y - point_H.y)
        if vector_HA[0]*vector_HB[0] + vector_HA[1]*vector_HB[1] > 0 :
            k_b = k_a - 1 if k_a > 0 else -1
            point_B = Point(coords[k_b]) if k_b != -1 else None
    elif k_a > 0:
        k_b = k_a - 1
        point_B = Point(coords[k_b])
        vector_HB = (point_B.x - point_H.x, point_B.y - point_H.y)
        if vector_HA[0]*vector_HB[0] + vector_HA[1]*vector_HB[1] > 0 :
            k_b = -1
            point_B = None
    else:
        k_b = -1
        point_B = None
    # Xử lý trường hợp là đường 1 chiều ( HA, HB không thể đi ngược chiều)
    if way_id in oneway_id  and k_b != -1:
        if type == 'start':
            if k_b > k_a:
                point_A = point_B
            point_B = None
        elif type == "target":
            if k_b < k_a:
                point_A = point_B
            point_B = None

    # Xử lý trường hợp điểm khởi đầu và điểm kết thúc xe buýt phải là điểm nằm bên phải
    if type == 'start':
        if k_b > k_a:
            point_A = point_B
        point_B = None
    elif type == "target":
        if k_b < k_a:
            point_A = point_B
        point_B = None
    return point_H, point_A, point_B, name


def get_children(point, name_start, name_target):
    gdf['distance'] = gdf['geometry'].distance(point)
    lines = gdf.loc[gdf['distance'] == 0]
    print('line:', list(lines['name'])[0])
    children = []
    if not lines.empty: # Nếu point đang nằm trên 1 đường nào đó
        for row in lines.itertuples(): # duyệt qua các đường chứa point ( có case: point là giao điểm của nhiều đường)
            geometry_value = row.geometry
            coords = geometry_value.coords
            list_point = [Point(coord) for coord in coords]
            idx = list_point.index(point)

            if idx > 0 and row.id not in oneway_id and list(lines['name'])[0] != name_start and list(lines['name'])[0] != name_target:
                children.append(list_point[idx-1])

            if idx < len(list_point) - 1: 
                children.append(list_point[idx+1])
    return children

