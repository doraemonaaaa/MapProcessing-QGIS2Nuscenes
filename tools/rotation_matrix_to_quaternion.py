import numpy as np

def rotation_matrix_to_quaternion(R):
    # 计算四元数的 w 部分
    w = 0.5 * np.sqrt(1 + R[0, 0] + R[1, 1] + R[2, 2])

    # 计算四元数的 x, y, z 部分
    x = 0.5 * np.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2])
    y = 0.5 * np.sqrt(1 - R[0, 0] + R[1, 1] - R[2, 2])
    z = 0.5 * np.sqrt(1 - R[0, 0] - R[1, 1] + R[2, 2])

    # 判断符号以确定正确的四元数分量
    if R[2, 1] - R[1, 2] < 0:
        x = -x
    if R[0, 2] - R[2, 0] < 0:
        y = -y
    if R[1, 0] - R[0, 1] < 0:
        z = -z

    # 返回四元数 (w, x, y, z)
    return np.array([w, x, y, z])

def quaternion_to_rotation_matrix(q):
    w, x, y, z = q
    # 计算旋转矩阵的每个元素
    R = np.array([
        [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
    ])
    return R

# 输入角度，单位为度
def get_rotation_matrix(axis, angle_deg):
    angle_rad = np.deg2rad(angle_deg)  # 将角度转换为弧度

    if axis == 'x':
        # 绕X轴旋转
        R = np.array([[1, 0, 0],
                      [0, np.cos(angle_rad), -np.sin(angle_rad)],
                      [0, np.sin(angle_rad), np.cos(angle_rad)]])
    
    elif axis == 'y':
        # 绕Y轴旋转
        R = np.array([[np.cos(angle_rad), 0, np.sin(angle_rad)],
                      [0, 1, 0],
                      [-np.sin(angle_rad), 0, np.cos(angle_rad)]])
    
    elif axis == 'z':
        # 绕Z轴旋转
        R = np.array([[np.cos(angle_rad), -np.sin(angle_rad), 0],
                      [np.sin(angle_rad), np.cos(angle_rad), 0],
                      [0, 0, 1]])
    
    else:
        raise ValueError("轴必须是 'x', 'y', 或 'z'")

    return R

# car coordinate to CAM_BACK
# R = np.array([[0, 1, 0],
#               [0, 0, -1],
#               [-1, 0, 0]])

# car coordinate to CAM_FRONT
R = np.array([[0, -1, 0],
              [0, 0, -1],
              [1, 0, 0]])

# z=-y,绕旋转后的y再旋转, 根据相机坐标系的定义，y正值旋转是顺时针方向
y_rotate_matrix = get_rotation_matrix('y', -240)
print("Y旋转矩阵:", y_rotate_matrix)
# 计算组合旋转矩阵
combined_rotation_matrix = np.dot(y_rotate_matrix, R)
print("最终组合旋转矩阵：", combined_rotation_matrix)
quaternion = rotation_matrix_to_quaternion(combined_rotation_matrix)
print("四元数:", quaternion)


# # 给定四元数 (w, x, y, z)
# q = [0.5037872666382278, -0.49740249788611096, -0.4941850223835201, 0.5045496097725578]
# # 计算旋转矩阵
# R = quaternion_to_rotation_matrix(q)
# print("旋转矩阵:\n", R)