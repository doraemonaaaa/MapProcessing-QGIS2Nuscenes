import numpy as np
from pyquaternion import Quaternion

# 给定的数值
ego_world_translation = np.array([5.971844426282407, 0.11134448866065963, 0.0])
ego_world_rotation = Quaternion(w=0.9999368449660043, x=0.0, y=0.0, z=-0.011238597752077771)

# 3D Box相对于Ego坐标系的数值
box_ego_translation = np.array([-3.9408597307957014, 0.32885810363408985, 0.29495090450320394])
box_ego_rotation = np.array([0, 0, 0.002931187467946428])  # 旋转是欧拉角，弧度制

# Step 1: 将Box的旋转（欧拉角）转换为四元数
box_ego_rotation_quat = Quaternion(axis=[1, 0, 0], angle=box_ego_rotation[0]) * \
                        Quaternion(axis=[0, 1, 0], angle=box_ego_rotation[1]) * \
                        Quaternion(axis=[0, 0, 1], angle=box_ego_rotation[2])

# Step 2: 将Box在Ego坐标系中的位置转换到世界坐标系
box_world_translation = ego_world_translation + ego_world_rotation.rotate(box_ego_translation)

# Step 3: 将Box的旋转（四元数）从Ego坐标系转换到世界坐标系
box_world_rotation = ego_world_rotation * box_ego_rotation_quat

# 计算Box的旋转的欧拉角（单位：度）, zyx格式
box_world_rotation_euler_angle = np.array(box_world_rotation.yaw_pitch_roll) * (180 / np.pi)

# 输出结果
print("3D Box Position in World Coordinates:", box_world_translation)
print("3D Box Rotation in World Coordinates (Quaternion):", box_world_rotation)
print("3D Box Rotation in World Coordinates (Euler Angles in Degrees):", box_world_rotation_euler_angle)
