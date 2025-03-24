import numpy as np

def quaternion_to_rotation_matrix(q):
    """
    将四元数转换为旋转矩阵
    :param q: 四元数，格式为 [qw, qx, qy, qz]
    :return: 3x3 旋转矩阵
    """
    qw, qx, qy, qz = q
    R = np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
    ])
    return R

def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    将俯仰角（roll, pitch, yaw）转换为旋转矩阵
    :param roll: 绕 x 轴的旋转角度（弧度）
    :param pitch: 绕 y 轴的旋转角度（弧度）
    :param yaw: 绕 z 轴的旋转角度（弧度）
    :return: 3x3 旋转矩阵
    """
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])
    
    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])
    
    # 组合旋转矩阵：R = Rz * Ry * Rx
    R = Rz @ Ry @ Rx
    return R

def build_extrinsic_matrix(rotation_matrix, translation):
    """
    构建外参矩阵
    :param rotation_matrix: 3x3 旋转矩阵
    :param translation: 3x1 位移向量 [x, y, z]
    :return: 4x4 外参矩阵
    """
    T = np.eye(4)
    T[:3, :3] = rotation_matrix
    T[:3, 3] = translation
    return T

# 示例 1：使用四元数计算外参矩阵
q = [0.6830127,  0.6830127,  0.1830127, -0.1830127]

translation = np.array([-0.090916, -0.112, -0.0524717])

# 将四元数转换为旋转矩阵
rotation_matrix = quaternion_to_rotation_matrix(q)
# 构建外参矩阵
extrinsic_matrix = build_extrinsic_matrix(rotation_matrix, translation)
print("外参矩阵（四元数）：\n", extrinsic_matrix)

# # 示例 2：使用俯仰角计算外参矩阵
# roll = np.radians(0)
# pitch = np.radians(0)
# yaw = np.radians(0)

# # 将俯仰角转换为旋转矩阵
# rotation_matrix = euler_to_rotation_matrix(roll, pitch, yaw)
# # 构建外参矩阵
# extrinsic_matrix = build_extrinsic_matrix(rotation_matrix, translation)
# print("外参矩阵（俯仰角）：\n", extrinsic_matrix)