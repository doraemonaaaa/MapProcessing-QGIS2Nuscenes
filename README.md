QGIS2Nuscenes map format

### python后处理对齐坐标系,QGIS2ROS

    ## 将 QGIS 坐标系转换为 ROS 的 origin 坐标系。
        - QGIS：Y 轴向下，左上角为原点
        - ROS：Y 轴向上，左下角为原点
        - 真实的 pose（米为单位）用 pixel 乘以 ros 的 resolution
        - ROS坐标系原点转到origin

### VAD需要的nuscenes的格式

    ## VAD涉及的nuscenes gt语义层

        1. （contour_class、polygon_class， 轮廓层，多边形层）语义层
            - road_divider（道路分隔线）
            - lane_divider（车道分隔线）
        2. 多边形（Polygon）语义层
            - drivable_area（可驾驶区域）提及，但是没有使用
            - road_segment（道路段）
            - lane（车道）
            - ped_crossing（人行横道）

    ## Nuscenes转VAD层关系：

        - boundary（边界）：并不是直接从一个名为 'boundary' 的语义层中提取，而是通过现有的轮廓层'road_segment' 和 'lane' 多边形层来构建。
        - Divider（分割）：通过nuscenes的'road_divider', 'lane_divider'得来
        - Ped_crossing（人行路）：通过nuscenes的'ped_crossing'得来

### geojson转换nuscenes的格式
    ## nuscenes的几何格式：
        - node: 最基础的元素，包含x,y坐标信息
        - line：两个node连接组成
        - polygon：多个node连接组成

    ## Method
         geojson解包nuscenes方法：语义--（包含）-> polygon | linestring ---（包含）--> node

    ## Scripts
        QGIS2Nuscenes 是最终的转换代码