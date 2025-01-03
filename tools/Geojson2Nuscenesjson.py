import geojson
import json
import uuid
from shapely.geometry import shape

class Geojson2Nuscenesjson:
    def __init__(self):
        """
        初始化语义层和数据结构。
        """
        # 修正拼写错误："road_divider" 而不是 "road_divder"
        self.nuscenes_semantic_layers = (
            "road_divider", "lane_divider", "road_segment", "lane", "ped_crossing"
        )
        # 初始化语义数据字典
        self.semantic_data = {layer: [] for layer in self.nuscenes_semantic_layers}
        # 初始化几何数据
        self.nodes = {}
        self.node_list = []
        self.line_list = []
        self.polygon_list = []

    def generate_token(self):
        """
        生成一个唯一的UUID作为token。
        UUID是一种标准的格式，用于在分布式系统中生成唯一的标识符，
        确保在不同系统或不同时间生成的ID不会重复。
        """
        return str(uuid.uuid4())

    def extract_semantics(self, geojson_data):
        """
        从GeoJSON的FeatureCollection中提取语义层名称。
        返回语义类型，如果不存在则返回'unknown'。
        """
        semantic_type = geojson_data.get('name', 'unknown')
        if semantic_type not in self.nuscenes_semantic_layers:
            semantic_type = 'unknown'
        return semantic_type

    def process_geometry(self, feature, semantic_type):
        """
        处理GeoJSON要素的几何数据，并根据语义类型分类存储。
        """
        geom = shape(feature['geometry'])
        properties = feature.get('properties', {})
        token = properties.get('token', self.generate_token())

        if geom.geom_type == 'Point':
            x, y = geom.x, geom.y
            node = {
                'token': token,
                'x': x,
                'y': y
            }
            self.node_list.append(node)
            self.nodes[token] = (x, y)

        elif geom.geom_type == 'LineString':
            coords = list(geom.coords)
            node_tokens = []
            for coord in coords:
                existing_token = None
                for tok, (x, y) in self.nodes.items():
                    if x == coord[0] and y == coord[1]:
                        existing_token = tok
                        break
                if existing_token is None:
                    new_token = self.generate_token()
                    node = {
                        'token': new_token,
                        'x': coord[0],
                        'y': coord[1]
                    }
                    self.node_list.append(node)
                    self.nodes[new_token] = coord
                    node_tokens.append(new_token)
                else:
                    node_tokens.append(existing_token)
            if len(node_tokens) >= 2:
                line = {
                    'token': token,
                    'node_tokens': [node_tokens[0], node_tokens[-1]]
                }
                self.line_list.append(line)

        elif geom.geom_type == 'Polygon':
            exterior_coords = list(geom.exterior.coords)
            exterior_node_tokens = []
            for coord in exterior_coords:
                existing_token = None
                for tok, (x, y) in self.nodes.items():
                    if x == coord[0] and y == coord[1]:
                        existing_token = tok
                        break
                if existing_token is None:
                    new_token = self.generate_token()
                    node = {
                        'token': new_token,
                        'x': coord[0],
                        'y': coord[1]
                    }
                    self.node_list.append(node)
                    self.nodes[new_token] = coord
                    exterior_node_tokens.append(new_token)
                else:
                    exterior_node_tokens.append(existing_token)

            # 处理孔洞（holes）
            holes = []
            for interior in geom.interiors:
                hole_coords = list(interior.coords)
                hole_tokens = []
                for coord in hole_coords:
                    existing_token = None
                    for tok, (x, y) in self.nodes.items():
                        if x == coord[0] and y == coord[1]:
                            existing_token = tok
                            break
                    if existing_token is None:
                        new_token = self.generate_token()
                        node = {
                            'token': new_token,
                            'x': coord[0],
                            'y': coord[1]
                        }
                        self.node_list.append(node)
                        self.nodes[new_token] = coord
                        hole_tokens.append(new_token)
                    else:
                        hole_tokens.append(existing_token)
                if hole_tokens:
                    holes.append(hole_tokens)

            polygon = {
                'token': token,
                'exterior_node_tokens': exterior_node_tokens,
                'holes': holes
            }
            self.polygon_list.append(polygon)

            # 如果是特定语义类型，如ped_crossing，添加到语义数据中
            if semantic_type in self.nuscenes_semantic_layers:
                semantic_entry = {
                    'token': self.generate_token(),
                    'polygon_token': token,
                    'road_segment_token': properties.get('road_segment_token', None)
                }
                self.semantic_data[semantic_type].append(semantic_entry)

    def assemble_nuscenes_map(self):
        """
        组合最终的NuScenesMap JSON结构。
        """
        nuscenes_map = {
            'node': self.node_list,
            'line': self.line_list,
            'polygon': self.polygon_list
        }

        # 添加语义层数据到NuScenesMap结构中
        for layer, data in self.semantic_data.items():
            if data:  # 仅添加非空的语义层
                nuscenes_map[layer] = data

        return nuscenes_map

    def convert(self, geojson_path, output_path):
        """
        执行从GeoJSON到NuScenesMap JSON的转换流程。
        """
        with open(geojson_path, 'r') as f:
            gj = geojson.load(f)

        # 提取语义类型
        semantic_type = self.extract_semantics(gj)
        print(f"Semantic type determined from FeatureCollection name: {semantic_type}")

        # 处理每个要素
        for feature in gj['features']:
            self.process_geometry(feature, semantic_type)

        # 组合最终的NuScenesMap JSON结构
        nuscenes_map = self.assemble_nuscenes_map()

        # 写入输出JSON文件
        with open(output_path, 'w') as f:
            json.dump(nuscenes_map, f, indent=4)

        print(f"Conversion complete. NuScenesMap JSON saved to {output_path}")

# 示例使用
if __name__ == "__main__":
    geojson_input = 'ped_crossing.geojson'  # 替换为您的GeoJSON文件路径
    nuscenes_output = 'output_nuscenes_map.json'  # 替换为您希望保存的JSON文件路径
    converter = Geojson2Nuscenesjson()
    converter.convert(geojson_input, nuscenes_output)
