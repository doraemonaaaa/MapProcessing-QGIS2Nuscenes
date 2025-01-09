import cv2

# 设置你连接的多个摄像头的索引
# 摄像头的索引通常是从0开始的
# 如果你有多个USB摄像头，可能需要尝试更高的索引号（比如1, 2, 3等）
camera_indices = [1, 2, 3, 4, 5]  # 假设你有两个摄像头

# 创建视频捕捉对象的列表
cameras = [cv2.VideoCapture(index) for index in camera_indices]

# 检查每个摄像头是否成功打开
for i, cam in enumerate(cameras):
    if not cam.isOpened():
        print(f"无法打开摄像头 {camera_indices[i]}")
        cameras[i] = None

# 启动多个摄像头并显示视频
while True:
    for i, cam in enumerate(cameras):
        if cam is not None:
            ret, frame = cam.read()
            if ret:
                # 在每个视频框中显示摄像头编号
                cv2.putText(frame, f"Camera {camera_indices[i]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow(f"Camera {camera_indices[i]}", frame)
            else:
                print(f"无法从摄像头 {camera_indices[i]} 读取视频帧")
    
    # 按'q'键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头和关闭所有窗口
for cam in cameras:
    if cam is not None:
        cam.release()

cv2.destroyAllWindows()
