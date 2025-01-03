import geopandas as gpd
import numpy as np
import yaml
import json
from PIL import Image  # 用于读取图像
import os

def load_yaml(file_path):
    """
    读取 YAML 配置文件
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

class QGIS2ROS:
    def __init__(self, geojson_data, resolution, origin, image_height):
        """
        初始化 QGIS2ROS 类实例。
        
        参数:
        - geojson_data: GeoJSON 数据（字典格式）
        - resolution: 分辨率（米/像素）
        - origin: 原点坐标 [x, y, z]
        - image_height: 图像高度（像素数）
        """
        self.geojson_data = geojson_data
        self.resolution = resolution
        self.origin = origin  # origin 是一个列表 [x, y, z]
        self.image_height = image_height
        self.origin_x, self.origin_y, _ = self.origin  # 提取 origin_x 和 origin_y

    def transform_point(self, qgis_coord):
        """
        将 QGIS 坐标系转换为 ROS 的 origin 坐标系。
        - QGIS：Y 轴向下，左上角为原点
        - ROS：Y 轴向上，左下角为原点
        - 真实的 pose（米为单位）用 pixel 乘以 ros 的 resolution
        - ROS坐标系原点转到origin
        """
        x_qgis, y_qgis = qgis_coord
        # 翻转 Y 轴（QGIS 的 Y 轴向下，ROS 的 Y 轴向上）
        y_flipped = self.image_height+ y_qgis
        # 像素转换到实际世界尺度
        x_ros = x_qgis * self.resolution
        y_ros = y_flipped * self.resolution
        # 将 ROS 坐标系原点移到 origin, origin是真实尺度
        x_real = x_ros - self.origin_x
        y_real = y_ros - self.origin_y
        return [x_real, y_real]


def main():
    # 加载 YAML 配置文件
    config = load_yaml('office_occupancy_map_coordinate.yaml')
    
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

    # 读取 QGIS 的 GeoJSON 文件
    input_geojson = 'test.geojson'
    try:
        geojson_gdf = gpd.read_file(input_geojson)
        geojson_data = geojson_gdf.__geo_interface__
    except Exception as e:
        print(f"无法读取 GeoJSON 文件: {e}")
        exit(1)

    # 创建 QGIS2ROS 类实例
    transformer = QGIS2ROS(
        geojson_data=geojson_data,
        resolution=resolution,
        origin=origin,
        image_height=image_height
    )

    # 执行坐标变换
    try:
        transformed_data = transformer.transform_geojson()
    except Exception as e:
        print(f"坐标转换过程中出现错误: {e}")
        exit(1)

    # 保存转换后的 GeoJSON 文件
    output_geojson_path = 'output_transformed.geojson'
    save_geojson(transformed_data, output_geojson_path)

    print(f"坐标变换已完成，并保存为 {output_geojson_path}")

if __name__ == "__main__":
    main()
