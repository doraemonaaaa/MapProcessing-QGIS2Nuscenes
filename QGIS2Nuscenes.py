import geojson
import json
import uuid
from shapely.geometry import shape
import geopandas as gpd
import numpy as np
import yaml
from PIL import Image  # 用于读取图像
import os


class Geojson2Nuscenesjson:
    def __init__(self, resolution, origin, image_height, image_width):
        """
        初始化语义层和数据结构。
        参数:
        - resolution: 分辨率（米/像素）
        - origin: 原点坐标 [x, y, z]
        - image_height: 图像高度（像素数）
        - image_width: 图像宽度（像素数）
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

        self.resolution = resolution
        self.origin = origin  # origin 是一个列表 [x, y, z]
        self.image_height = image_height
        self.image_width = image_width
        self.origin_x, self.origin_y, _ = self.origin  # 提取 origin_x 和 origin_y

    def transform_point(self, x, y, coord):
        """
        将 QGIS 坐标系转换为 ROS 的 origin 坐标系。
        - QGIS：Y 轴向下，左上角为原点
        - ROS：Y 轴向上，左下角为原点
        - 真实的 pose（米为单位）用 pixel 乘以 ros 的 resolution
        - ROS坐标系原点转到origin
        """
        if coord:
            x_qgis, y_qgis = coord
        else:
            x_qgis, y_qgis = x, y
        # 翻转 Y 轴（QGIS 的 Y 轴向下，ROS 的 Y 轴向上）
        y_flipped = self.image_height + y_qgis
        # 像素转换到实际世界尺度
        x_ros = x_qgis * self.resolution
        y_ros = y_flipped * self.resolution
        # 将 ROS 坐标系原点移到 origin, origin是真实尺度
        x_real = x_ros - self.origin_x
        y_real = y_ros - self.origin_y
        return [x_real, y_real]

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
            x, y = self.transform_point(geom.x, geom.y)  # transform coordinates
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
                coord = self.transform_point(None, None, coord)  # transform coordinates
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
                coord = self.transform_point(None, None, coord)  # transform coordinates
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

            # 根据不同的语义类型，创建不同的语义数据结构
            if semantic_type in self.nuscenes_semantic_layers:
                if semantic_type == 'ped_crossing':
                    semantic_entry = {
                        'token': self.generate_token(),
                        'polygon_token': token,
                        'road_segment_token': properties.get('road_segment_token', None)
                    }
                    self.semantic_data[semantic_type].append(semantic_entry)
                elif semantic_type == 'road_segment':
                    semantic_entry = {
                        'token': self.generate_token(),
                        'polygon_token': token,
                        'is_intersection': properties.get('is_intersection', False),
                        'drivable_area_token': properties.get('drivable_area_token', "")
                    }
                    self.semantic_data[semantic_type].append(semantic_entry)
                elif semantic_type == 'lane':
                    # 假设 left_divider_node_token 和 right_divider_node_token 是列表
                    left_dividers = properties.get('left_divider_node_tokens', ["unused"] * 4)
                    right_dividers = properties.get('right_divider_node_tokens', ["unused"])

                    semantic_entry = {
                        'token': self.generate_token(),
                        'polygon_token': token,
                        'lane_type': properties.get('lane_type', "CAR"),
                        'from_edge_line_token': properties.get('from_edge_line_token', "unused"),
                        'to_edge_line_token': properties.get('to_edge_line_token', "unused"),
                        'left_lane_divider_segments': [
                            {
                                'node_token': node_token,
                                'segment_type': properties.get('left_segment_type', "DOUBLE_DASHED_WHITE")
                            } for node_token in left_dividers
                        ],
                        'right_lane_divider_segments': [
                            {
                                'node_token': node_token,
                                'segment_type': properties.get('right_segment_type', "DOUBLE_DASHED_WHITE")
                            } for node_token in right_dividers
                        ]
                    }
                    self.semantic_data[semantic_type].append(semantic_entry)
                elif semantic_type == 'road_divider' or semantic_type == 'lane_divider':
                    if semantic_type == 'road_divider':
                        semantic_entry = {
                            'token': self.generate_token(),
                            'line_token': properties.get('line_token', "unused"),
                            'road_segment_token': properties.get('road_segment_token', None)
                        }
                    else:  # lane_divider
                        semantic_entry = {
                            'token': self.generate_token(),
                            'line_token': properties.get('line_token', "unused"),
                            'lane_divider_segments': [
                                {
                                    'node_token': properties.get('divider_node_token', "unused"),
                                    'segment_type': properties.get('segment_type', "DOUBLE_DASHED_WHITE")
                                }
                            ]
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

        # 添加canvas_edge到NuScenesMap结构中
        canvas_edge = [self.image_width / 10.0, self.image_height / 10.0]
        nuscenes_map['canvas_edge'] = canvas_edge

        return nuscenes_map

    def merge_maps(self, existing_map, new_map):
        """
        将新的NuScenesMap数据合并到现有的NuScenesMap数据中。
        """
        # 合并节点
        existing_map['node'].extend(new_map.get('node', []))

        # 合并线
        existing_map['line'].extend(new_map.get('line', []))

        # 合并多边形
        existing_map['polygon'].extend(new_map.get('polygon', []))

        # 合并语义层
        for layer in self.nuscenes_semantic_layers:
            if layer in new_map:
                if layer not in existing_map:
                    existing_map[layer] = []
                existing_map[layer].extend(new_map[layer])

        # 合并 canvas_edge
        if 'canvas_edge' in new_map:
            if 'canvas_edge' in existing_map:
                existing_canvas = existing_map['canvas_edge']
                new_canvas = new_map['canvas_edge']
                if existing_canvas != new_canvas:
                    raise ValueError(
                        f"Canvas edge mismatch: existing {existing_canvas} vs new {new_canvas}"
                    )
                # 如果相同，不做任何操作
            else:
                existing_map['canvas_edge'] = new_map['canvas_edge']

        return existing_map

    def convert(self, geojson_path, output_path):
        """
        执行从GeoJSON到NuScenesMap JSON的转换流程。
        如果输出文件已存在，则将新的内容添加到现有内容中。
        """
        # 生成新的NuScenesMap
        with open(geojson_path, 'r') as f:
            gj = geojson.load(f)

        # 提取语义类型
        semantic_type = self.extract_semantics(gj)
        print(f"Semantic type determined from FeatureCollection name: {semantic_type}")

        # 处理每个要素
        for feature in gj['features']:
            self.process_geometry(feature, semantic_type)

        # 组合新的NuScenesMap JSON结构
        new_nuscenes_map = self.assemble_nuscenes_map()

        # 检查输出文件是否存在
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    existing_map = json.load(f)
                print(f"已检测到现有的输出文件，正在合并内容。")
            except Exception as e:
                print(f"无法读取现有的输出文件: {e}")
                print("将创建一个新的输出文件。")
                existing_map = {}
        else:
            existing_map = {}

        # 如果存在现有内容，进行合并
        if existing_map:
            combined_map = self.merge_maps(existing_map, new_nuscenes_map)
        else:
            combined_map = new_nuscenes_map

        # 写入输出JSON文件
        with open(output_path, 'w') as f:
            json.dump(combined_map, f, indent=4)

        print(f"Conversion complete. NuScenesMap JSON saved to {output_path}")

def load_yaml(file_path):
    """
    读取 YAML 配置文件
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# 示例使用
if __name__ == "__main__":
    geojson_input = 'ped_crossing.geojson'  # 替换为您的GeoJSON文件路径
    ros_yaml_input = 'office_occupancy_map_coordinate.yaml'
    nuscenes_output = 'output_nuscenes_map.json'  # 替换为您希望保存的JSON文件路径
    # 加载 YAML 配置文件
    config = load_yaml(ros_yaml_input)
    
    # 提取所需的信息
    image_path = config['image']
    resolution = config['resolution']
    origin = config['origin']  # origin 是一个列表 [x, y, z]
    negate = config.get('negate', 0)  # 如果 negate 不存在，默认为 0
    occupied_thresh = config.get('occupied_thresh', 0.65)  # 默认阈值
    free_thresh = config.get('free_thresh', 0.196)  # 默认阈值
    print(f"*********resolution={resolution}, origin={origin}, negate={negate}, occupied_thresh={occupied_thresh}*******")

    # 读取图像以获取图像高度（像素数）
    try:
        with Image.open(image_path) as img:
            image_width, image_height = img.size
            print(f"图像宽度: {image_width}px, 图像高度: {image_height}px")
    except Exception as e:
        print(f"无法读取图像文件: {e}")
        exit(1)
    
    converter = Geojson2Nuscenesjson(
        resolution=resolution,
        origin=origin,
        image_height=image_height,
        image_width=image_width  # 新增的参数
    )
    converter.convert(geojson_input, nuscenes_output)
