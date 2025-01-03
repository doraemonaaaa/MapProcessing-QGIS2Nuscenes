import json
from shapely.geometry import shape, mapping
from pyproj import Transformer
import uuid

# 定义原点（以西南角为原点的经纬度）
ORIGIN_LAT = 1.2782562240223188  # 例如，singapore-queenstown 的纬度
ORIGIN_LON = 103.76741409301758  # 例如，singapore-queenstown 的经度

# 初始化投影转换器（将经纬度转换为平面坐标，例如使用 UTM）
transformer = Transformer.from_crs("epsg:4326", "epsg:32648", always_xy=True)  # 选择适当的 UTM 区

def generate_token():
    return str(uuid.uuid4())

def convert_geojson_to_nuscenesmap(geojson_path, nuscenesmap_path):
    with open(geojson_path, 'r') as f:
        geojson = json.load(f)
    
    nuscenes_map = {
        "node_list": [],
        "line_list": [],
        "polygon_list": [],
        # 添加其他必要的图层
    }
    
    node_dict = {}
    
    for feature in geojson['features']:
        geom = shape(feature['geometry'])
        properties = feature.get('properties', {})
        
        if geom.geom_type == 'Point':
            # 处理节点
            lon, lat = geom.x, geom.y
            x, y = transformer.transform(lon, lat)
            # 相对于原点的坐标
            local_x = x - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[0]
            local_y = y - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[1]
            
            token = generate_token()
            node = {
                "token": token,
                "x": local_x,
                "y": local_y
            }
            nuscenes_map["node_list"].append(node)
            node_dict[feature['id']] = token  # 假设每个点有唯一的 id
        
        elif geom.geom_type == 'LineString':
            # 处理线条
            node_tokens = []
            for point in geom.coords:
                lon, lat = point
                x, y = transformer.transform(lon, lat)
                local_x = x - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[0]
                local_y = y - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[1]
                point_id = f"{feature['id']}_{point}"
                if point_id not in node_dict:
                    token = generate_token()
                    node = {
                        "token": token,
                        "x": local_x,
                        "y": local_y
                    }
                    nuscenes_map["node_list"].append(node)
                    node_dict[point_id] = token
                node_tokens.append(node_dict[point_id])
            
            line = {
                "token": generate_token(),
                "node_tokens": node_tokens
            }
            nuscenes_map["line_list"].append(line)
        
        elif geom.geom_type == 'Polygon':
            # 处理多边形
            exterior = geom.exterior.coords
            exterior_tokens = []
            for point in exterior:
                lon, lat = point
                x, y = transformer.transform(lon, lat)
                local_x = x - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[0]
                local_y = y - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[1]
                point_id = f"{feature['id']}_exterior_{point}"
                if point_id not in node_dict:
                    token = generate_token()
                    node = {
                        "token": token,
                        "x": local_x,
                        "y": local_y
                    }
                    nuscenes_map["node_list"].append(node)
                    node_dict[point_id] = token
                exterior_tokens.append(node_dict[point_id])
            
            holes = []
            for interior in geom.interiors:
                hole_tokens = []
                for point in interior.coords:
                    lon, lat = point
                    x, y = transformer.transform(lon, lat)
                    local_x = x - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[0]
                    local_y = y - transformer.transform(ORIGIN_LON, ORIGIN_LAT)[1]
                    point_id = f"{feature['id']}_hole_{point}"
                    if point_id not in node_dict:
                        token = generate_token()
                        node = {
                            "token": token,
                            "x": local_x,
                            "y": local_y
                        }
                        nuscenes_map["node_list"].append(node)
                        node_dict[point_id] = token
                    hole_tokens.append(node_dict[point_id])
                holes.append(hole_tokens)
            
            polygon = {
                "token": generate_token(),
                "exterior_node_tokens": exterior_tokens,
                "holes": holes
            }
            nuscenes_map["polygon_list"].append(polygon)
        
        # 处理其他几何类型和非几何图层（如 drivable_area 等）根据需求扩展
    
    # 保存为 NuScenesMap 格式的 JSON 文件
    with open(nuscenesmap_path, 'w') as f:
        json.dump(nuscenes_map, f, indent=4, ensure_ascii=False)
    
    print(f"转换完成，保存为 {nuscenesmap_path}")

# 示例用法
geojson_input = 'test22.geojson'
nuscenesmap_output = 'output_nuscenesmap.json'
convert_geojson_to_nuscenesmap(geojson_input, nuscenesmap_output)
