import numpy as np
from scipy.spatial.transform import Rotation as R

# 给定的数值
ego_world_translation = np.array([5.971844426282407, 0.11134448866065963, 0.0])
ego_world_rotation = np.array([0.0, 0.0, -0.011238597752077771, 0.9999368449660043])  # 四元数表示的旋转

# 3D Box相对于Ego坐标系的数值
box_ego_translation = np.array([-3.9408597307957014, 0.32885810363408985, 0.29495090450320394])
box_ego_rotation = np.array([0, 0, 0.002931187467946428])  # 旋转是欧拉角，弧度制

# Step 1: 将Ego坐标系的旋转转换为四元数
ego_rotation = R.from_quat(ego_world_rotation)

# Step 2: 将Box的旋转（欧拉角）转换为四元数
box_ego_rotation_quat = R.from_euler('xyz', box_ego_rotation).as_quat()

# Step 3: 将Box在Ego坐标系中的位置转换到世界坐标系
box_world_translation = ego_world_translation + ego_rotation.apply(box_ego_translation)

# Step 4: 将Box的旋转（四元数）从Ego坐标系转换到世界坐标系
box_world_rotation = ego_rotation * R.from_quat(box_ego_rotation_quat)

# 计算Box的旋转的欧拉角（单位：度）
box_world_rotation_euler_angle = box_world_rotation.as_euler('xyz', degrees=True)

# 输出结果
print("3D Box Position in World Coordinates:", box_world_translation)
print("3D Box Rotation in World Coordinates (Quaternion):", box_world_rotation.as_quat())
print("3D Box Rotation in World Coordinates (Euler Angles in Degrees):", box_world_rotation_euler_angle)
