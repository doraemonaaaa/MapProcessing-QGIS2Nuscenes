
## nuscenes_map_my_test_ok.json
    其他的几何token设置的是unused，坐标设置的无限大，就不可能落到gt，然后还能跑通，说明是真实标注ped_crossing的作用
    - ego_pose = 0
    - bev_w, bev_h > 10, 10

## unused_template.json
    全部都是Unused，不能训练，但可以作为地图的模板，后面写入所需的gt semantic layer