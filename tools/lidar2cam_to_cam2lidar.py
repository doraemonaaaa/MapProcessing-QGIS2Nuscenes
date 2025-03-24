import numpy as np
from pyquaternion import Quaternion  # 使用 pyquaternion 库来处理四元数

# 给定的 lidar2cam 变换
lidar2cam_translation = np.array([-0.090916, -0.112, -0.0524717])
lidar2cam_rotation = Quaternion([0.6771052026951145,0.6822076590821752,-0.185991155406967,0.20378553551027107])  # 四元数格式 [w, x, y, z]

# 计算 cam2lidar 变换
# 旋转部分：四元数的共轭 (反转符号)
cam2lidar_rotation = lidar2cam_rotation.conjugate

# 位移部分：反转位移
cam2lidar_translation = -lidar2cam_translation

# 输出 cam2lidar 变换
print("cam2lidar Translation:", cam2lidar_translation)
# 将四元数输出为 [w, x, y, z] 格式，保留更多小数位
quat_list = [
    float("{:.10f}".format(cam2lidar_rotation.w)),
    float("{:.10f}".format(cam2lidar_rotation.x)),
    float("{:.10f}".format(cam2lidar_rotation.y)),
    float("{:.10f}".format(cam2lidar_rotation.z))
]

print("cam2lidar Rotation (Quaternion) [w, x, y, z]:", quat_list)