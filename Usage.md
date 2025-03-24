QGIS2Nuscenes map format

# python后处理对齐坐标系,QGIS2ROS
    ## 坐标系记录
        ### 地图
            - QGIS地图，左上角原点，x右y下
            - ROS地图，左下角原点，x右y上
        ### 世界坐标系
            - ROS世界和issac sim世界坐标系， x前y左
            - NuscenesBEV，y前x右

    ## 将 QGIS 坐标系转换为 ROS 的 origin 坐标系。
        - QGIS地图：Y 轴向下，左上角为原点
        - ROS地图：Y 轴向上，左下角为原点
        - 真实的 pose（米为单位）用 pixel 乘以 ros 的 resolution
        - ROS地图坐标系原点转到origin
        - ROS地图坐标系转ROS世界坐标系

    ## 再将ROS坐标系转为NuscenesBEV坐标系
        - ROS世界和issac sim世界坐标系 ---> NuscenesBEV坐标系

# VAD需要的nuscenes的格式

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

# RobotAD
    ## RobotAD主要关注boundary，所以标注contour类型，contour类型中选取road_divider，仅road_divider会被标注(line type)

# geojson转换nuscenes的格式
    ## nuscenes的几何格式：
        - node: 最基础的元素，包含x,y坐标信息
        - line：两个node连接组成
        - polygon：多个node连接组成

    ## Method
         geojson解包nuscenes方法：语义--（包含）-> polygon | linestring ---（包含）--> node

    ## Scripts
        QGIS2Nuscenes 是最终的转换代码


# Usage
    ## copy test/unused_template.json to folder and rename it to the output_nuscenes_map.json
    ## prepare for the map annotation(geojson) and map.png, map.yaml 
    ## run the src/QGIS2Nuscenes.py, if you wanna got road_divider annotation to output_nuscenes_map.json, naming your annotation to road_divider

    ## we only use the polygon type annotation type(road_segment, not lane) as the boundary
    road_segment: polygon, which always anootate the boundary, where there is a block, then there is a boundary

# Map annotation methods
    ## 由于polygon地难以控制性，和QGIS地polygon交叉不融合性，我们分别进行两步骤标图
    一、polygon标注内外轮廓（polygon更方便）
        ① 用第一层road_segment out先把外部boundary框起
        ② 用第二层road_segment holes吧内部地boundary框起
    二、融合内外标注
        1、融合polygon内外标注（遗弃，由于polygon的内外组合太复杂不好实现）
            ③ 用nuscenes定义的polygon内外部方法组合polygon，一般情况下out只有一个polygon（密闭环境下），所以只需要把holes的polygon全部移到out的那个polygon的holes里面就行了"holes"[{"node_tokens": [] }, {"node_tokens": []}]'
            ④ 内部的polygon也要写在polygon里面，内部polygon也可以写holes，然后以此嵌套，可以说是按层来
        2、融合line内外标注
            ① 将一中生成的内外polygon通过polygon_to_lines转换为multiLineString
            ② 通过merge融合
            ③ 再通过vector/geometry Tools/Multipart to singleparts将其转换为LineString（代码只能处理LineString）