import numpy as np
from scipy.spatial.transform import Rotation as R

# 给定四元数 (w, x, y, z)
w = 0
x = 0
y = -0.3
z = 0.92
# 创建一个四元数对象
quat = [w, x, y, z]
# 将四元数转换为欧拉角
rotation = R.from_quat(quat)
# 获取欧拉角，假设使用 ZYX 顺序（Yaw, Pitch, Roll）
euler_angles = rotation.as_euler('zyx', degrees=True)
# 打印结果，x, y, z顺序
print(f"Roll (φ): {euler_angles[2]}°")
print(f"Pitch (θ): {euler_angles[1]}°")
print(f"Yaw (ψ): {euler_angles[0]}°")

# 假设给定的欧拉角 (Roll, Pitch, Yaw)
roll = 0  # 以度为单位
pitch = 0
yaw = 0.002931187467946428
# 将欧拉角转换为四元数（使用 xyz 顺序）
euler_angles_input = [roll, pitch, yaw]
rotation_from_euler = R.from_euler('xyz', euler_angles_input, degrees=True)
# 转换后的四元数
quat_from_euler = rotation_from_euler.as_quat()
# 打印转换后的四元数
print(f"转换得到的四元数 (w, x, y, z): {quat_from_euler}")
