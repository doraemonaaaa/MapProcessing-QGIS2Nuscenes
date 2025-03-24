import json
import uuid
import yaml
from PIL import Image  # 用于读取图像
import os
import math


# - qgis默认x右y下，图片左上角
# - ISAAC默认x右y上，图片左下角
# - ROS地图图片为(x右，y上)，右上角为坐标原点

# x, y, 将ISSAC图片/ROS图片里面的坐标系（x右y上）/(x右y上)转换为实际issac里面的右手坐标系（未知，实际情况）,正值逆时针旋转（右手定则）
# full_warehouse = (180, 180) # Isaac
# AIR_F1 = (135, 135) # ROS
# AIR_B1 = (-5， -5) # ROS
# AIR_G = (45, 45 # ROS)
# AIR_F11 = (155, 155) # ROS
ros2issac_axis_mapping = (155, 155)  # ROS以ROS图片的进行调整, ISAAC以ISAAC图片进行调整epoch_name = "20250122_192629"
epoch_name = "20250122_192629"
map_name = "AIR_F11"
IS_ROS = True

# 配置文件
# dataset
dataset_foldet = r'data/Dataset/' + epoch_name  # 根路径
pose_in_image_json_path = r'data/pose_in_image/' + epoch_name + '/pose_in_image.json'  # 根路径
lidar_folder = dataset_foldet + r'/samples/LIDAR_TOP'
sample_data_path = dataset_foldet + r'/sample_data.json'
sample_json_path = dataset_foldet + r'/sample.json'
ego_pose_path = dataset_foldet + r'/ego_pose.json'

# map
resource_root = 'resource/' + map_name + '/'
geojson_input = resource_root + 'road_divider.geojson'  # 替换为您的GeoJSON文件路径
ros_yaml_input = resource_root + map_name + '.yaml'
template_path = 'template/unused_template.json'

ego_pose_output_path = "data/ego_pose.json"

def find_json_with_key(search_key, search_value, json_datas)-> json:

    # 查找包含指定键值对的JSON对象
    result = None
    for obj in json_datas:
        if obj.get(search_key) == search_value:
            result = obj
            break
        
    return result

def find_all_json_with_key(search_key, search_value, json_datas):
    """
    查找所有包含指定键值对的 JSON 对象，并提取指定字段的值。

    参数:
        search_key (str): 要查找的键。
        search_value (any): 要匹配的值。
        json_datas (list): 包含多个 JSON 对象的列表。

    返回:
        list: 包含所有匹配 JSON 对象的列表。
    """
    # 查找所有匹配的 JSON 对象
    matched_jsons = [obj for obj in json_datas if obj.get(search_key) == search_value]
    return matched_jsons

class Geojson2Nuscenesjson:
    def __init__(self, 
                 resolution, origin, image_height, image_width, is_ros=IS_ROS,
                 axis_mapping=ros2issac_axis_mapping,
                 ):
        """
        初始化语义层和数据结构。
        参数:
        - resolution: 分辨率（米/像素）
        - origin: 原点坐标 [x, y, z]
        - image_height: 图像高度（像素数）
        - image_width: 图像宽度（像素数）
        """
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
        
        # 用于将qgis的坐标系方向对齐到issac的坐标系方向，角度顺时针为正旋转，数据结构：(x轴旋转方向，y轴旋转方向)，进行qgis->ros->issac or real_world
        # - qgis默认x右y下，图片左上角
        # - ROS默认x右y上，图片右上角
        # - ISAAC默认x右y上，图片左下角
        # - issac或者real world原点旋转随机按照实际情况来
        # - axis_mapping 用于 ros -> issac 坐标系方向
        self.axis_mapping = axis_mapping
        self.is_ros = is_ros

    def transform_point(self, x, y, coord):
        """
        将 QGIS/普通图像 坐标系转换为 ROS/Isaac 的 origin 坐标系。
        再将 ROS/Isaac 坐标转换为 Issac 或 real world 坐标（基于 self.axis_mapping）。
        - qgis默认x右y上，图片左上角
        - ROS默认x左y下，图片左下角
        - ISAAC默认x右y上，图片左下角
        - 真实的 pose（米为单位）用 pixel 乘以 ros 的 resolution
        - ROS坐标系原点转到origin
        - ROS--->Issac或者real world的coordinate方向
        
        再将世界坐标转为bev坐标
        - Issac或者real world ---> BEV(和QGIS一样)
        """
        if coord:
            x_qgis, y_qgis = coord
        else:
            x_qgis, y_qgis = x, y
            
        if self.is_ros:  # ROS地图yaml
            ### Step 1: QGIS -> ROS
            # 翻转 Y 轴（QGIS 的 Y 轴向下，ROS 的 Y 轴向上）
            y_flipped = self.image_height + y_qgis
            # 像素转换到实际世界尺度（ROS的分辨率是每个像素对应多少米）
            x_ros = x_qgis * self.resolution
            y_ros = y_flipped * self.resolution
            # 将 ROS 坐标系原点移到 origin
            x_ros_real = x_ros + self.origin_x
            y_ros_real = y_ros + self.origin_y
            ### Step 2: Isaac -> Isaac/real world
            # 应用 self.axis_mapping（角度旋转）
            x_rotation, y_rotation = self.axis_mapping  # 获取 X 和 Y 轴的旋转角度（以度为单位）
            theta_x = math.radians(x_rotation)  # 将角度转换为弧度
            theta_y = math.radians(y_rotation)  # 将角度转换为弧度
            # 应用旋转矩阵公式
            x_transformed = x_ros_real * math.cos(theta_x) - y_ros_real * math.sin(theta_x)
            y_transformed = x_ros_real * math.sin(theta_y) + y_ros_real * math.cos(theta_y)
        else: #isaac地图yaml
            ### Step 1: QGIS -> Isaac
            # 翻转 Y 轴（QGIS 的 Y 轴向下，Isaac 的 Y 轴向上）
            y_flipped = self.image_height + y_qgis
            # 像素转换到实际世界尺度
            x_isaac = x_qgis * self.resolution
            y_isaac = y_flipped * self.resolution
            # 将 Isaac 坐标系原点移到 origin, origin是真实尺度
            x_isaac_real = x_isaac - self.origin_x
            y_isaac_real = y_isaac - self.origin_y
            
            ### Step 2: Isaac -> Issac/real world
            # 应用 self.axis_mapping（角度旋转）
            x_rotation, y_rotation = self.axis_mapping  # 获取 X 和 Y 轴的旋转角度（以度为单位）
            theta_x = math.radians(x_rotation)  # 将角度转换为弧度
            theta_y = math.radians(y_rotation)  # 将角度转换为弧度
            # 应用旋转矩阵公式
            x_transformed = x_isaac_real * math.cos(theta_x) - y_isaac_real * math.sin(theta_x)
            y_transformed = x_isaac_real * math.sin(theta_y) + y_isaac_real * math.cos(theta_y)
        
        return [x_transformed, y_transformed]

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
            node_tokens = []  # 存储节点 token 列表
            for coord in coords:
                coord = self.transform_point(None, None, coord)  # 转换坐标
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
                # 创建 line 数据
                line_token = self.generate_token()
                line = {
                    'token': line_token,
                    'node_tokens': node_tokens  # 完整的节点列表
                }
                self.line_list.append(line)

                # **road_divider** 结构
                if semantic_type == 'road_divider':
                    semantic_entry = {
                        'token': self.generate_token(),  # 唯一标识符
                        'line_token': line_token,
                        'road_segment_token': properties.get('road_segment_token', None)
                    }
                    self.semantic_data[semantic_type].append(semantic_entry)

                # **lane_divider** 结构
                elif semantic_type == 'lane_divider':
                    lane_divider_segments = [
                        {
                            'node_token': node_token,
                            'segment_type': properties.get('segment_type', "DOUBLE_DASHED_WHITE")
                        } for node_token in node_tokens
                    ]
                    semantic_entry = {
                        'token': self.generate_token(),
                        'line_token': line_token,
                        'lane_divider_segments': lane_divider_segments
                    }
                    self.semantic_data[semantic_type].append(semantic_entry)


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
                            #'drivable_area_token': properties.get('drivable_area_token', token)  # 改为实际的多边形 token
                            'drivable_area_token': ""
                        }
                        self.semantic_data[semantic_type].append(semantic_entry)
                elif semantic_type == 'lane':
                    # 使用几何结构生成左右分隔线 token 列表，而非 "unused"
                    left_dividers = [self.generate_token() for _ in range(2)]
                    right_dividers = [self.generate_token() for _ in range(2)]
                    
                    semantic_entry = {
                        'token': self.generate_token(),
                        'polygon_token': token,
                        'lane_type': properties.get('lane_type', "CAR"),
                        'from_edge_line_token': self.generate_token(),  # 基于 line token 生成，而不是 "unused"
                        'to_edge_line_token': self.generate_token(),
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

        # 添加canvas_edge（真实尺寸）到NuScenesMap结构中
        canvas_edge = [self.image_width * self.resolution, self.image_height  * self.resolution]
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
        
    def get_world_position(self, x, y):
        return self.transform_point(x, y)
        
        

def load_yaml(file_path):
    """
    读取 YAML 配置文件
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

# 示例使用
if __name__ == "__main__":    
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
        image_width=image_width
    )

    lidar_file_names = os.listdir(lidar_folder)
    # 加载 sample_data.json 文件
    with open(sample_data_path, 'r', encoding='utf-8') as f:
        sample_data_json_data = json.load(f)
    # 加载 sample.json 文件
    with open(sample_json_path, 'r', encoding='utf-8') as f:
        sample_json_data = json.load(f)
    # 加载 ego_pose.json 文件
    with open(ego_pose_path, 'r', encoding='utf-8') as f:
        ego_pose_json_data = json.load(f)
        
    # 排序雷达文件名
    lidar_file_names_sorted = sorted(  # 提取时间戳并排序（按主时间戳和次时间戳组成的元组排序）
        lidar_file_names,
        key=lambda x: tuple(map(int, x.split("__")[-1].split(".")[0].split("_")))
    )
    # for idx, filename in enumerate(lidar_file_names_sorted):  # 打印排序结果（序号从0开始）
    #     print(f"Index {idx}: {filename}")

    try:
        with open(pose_in_image_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error in file: {pose_in_image_json_path}")
        print(f"Error details: {e}")
        with open(pose_in_image_json_path, 'r', encoding='utf-8') as f:
            print(f"File content: {f.read()}")
        raise  # 重新抛出异常，终止程序
        
    lidar_file_numbers_and_poses = {}
    if data:
        for entry in data:
            lidar_file_name = entry.get("lidar_file_name")
            pose_in_map_pixel = entry.get("pose_in_map_pixel")
            
            if not lidar_file_name or not pose_in_map_pixel:
                raise ValueError("Lidar file or pose_in_map_pixel not found")
            else:
                # 提取数字部分并转换为整数
                lidar_file_number = int(''.join(filter(str.isdigit, lidar_file_name)))
                # 将 lidar_file_number 作为键，pose_in_map_pixel 作为值存储到字典中
                lidar_file_numbers_and_poses[lidar_file_number] = pose_in_map_pixel
                
    ego_pose_json_data_changed = []
    for lidar_file_number, pose_in_map_pixel in lidar_file_numbers_and_poses.items():
        
        lidar_file_name = lidar_file_names_sorted[lidar_file_number]
        
        '''BUG'''
        # 由于数据的bug，将_转换为:,__不被替换
        # 先将 '__' 替换为一个临时标记，比如 '__TEMP__'
        temp_file_name = lidar_file_name.replace("__", "'")
        # 然后将单个 '_' 替换为 ':'
        corrected_file_name = temp_file_name.replace("_", ":")
        # 最后将临时标记 '__TEMP__' 替换回 '__'
        corrected_file_name = corrected_file_name.replace("'", "__") 
        s = corrected_file_name
        # 1. 从后往前查找最后两个 ':'，并替换倒数两个 ':'
        parts = s.rsplit(":", 2)
        if len(parts) >= 3:
            s = ":".join(parts[:-2]) + "_" + parts[-2] + "_" + parts[-1]
        # 2. 然后将第一个 ':' 替换为 '_'
        first_colon_index = s.find(":")
        if first_colon_index != -1:
            s = s[:first_colon_index] + "_" + s[first_colon_index+1:]
        corrected_file_name = s

        # 获得sample_data_token from LIDAR filename
        corr_sample_data_json = find_json_with_key("filename", corrected_file_name, sample_data_json_data)
        #print(annotation_json_obj)
        sample_token = corr_sample_data_json["sample_token"]
        #print(sample_token)
        corr_sample_json = find_json_with_key("token", sample_token, sample_json_data)
        
        # 寻找这个sample里面所有的json
        sample_jsons = find_all_json_with_key("sample_token", corr_sample_json, sample_data_json_data)
        ego_pose_tokens = [obj.get("ego_pose_token") for obj in sample_jsons]
        
        # 根据位置像素计算世界坐标
        image_x = pose_in_map_pixel[0]
        image_y = pose_in_map_pixel[1]
        x_world, y_world = converter.get_world_position(image_x, image_y)  # get world postion from image
        
        # 修复所有的ego_pose
        for ego_pose_token in ego_pose_tokens:
            ego_pose_json = find_json_with_key("token", ego_pose_token, ego_pose_json_data)
            if ego_pose_json:
                ego_pose_json["translation"] = [x_world, y_world, 0]  # 更新 translation 字段
                ego_pose_json_data_changed.append(ego_pose_json)
            else:
                print(f"未找到 token 为 {ego_pose_token} 的 ego_pose 数据")
                
    with open(ego_pose_path, 'w', encoding='utf-8') as f:
        json.dump(ego_pose_json_data_changed, f, ensure_ascii=False, indent=4)
    