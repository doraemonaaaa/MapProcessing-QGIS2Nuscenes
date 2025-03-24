import cv2
import os

# 视频文件路径
video_path = r"D:\vis_VAD.mp4"
# 存储提取帧的文件夹
output_dir = 'extracted_frames'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 打开视频文件
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("无法打开视频文件")
    exit()

# 获取视频的帧率
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"视频帧率: {fps} fps")

# 设定要抽取的时间段：从 1分50秒 到 1分51秒
start_time = 1 * 60 + 27   # 1分50秒转换为秒
end_time = start_time + 1  # 1秒钟的时长

# 计算对应的帧索引
start_frame = int(start_time * fps)
end_frame = int(end_time * fps)

# 设置视频的起始帧位置
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

current_frame = start_frame
while cap.isOpened() and current_frame < end_frame:
    ret, frame = cap.read()
    if not ret:
        break

    # 构造输出文件名
    frame_filename = os.path.join(output_dir, f"frame_{current_frame}.jpg")
    cv2.imwrite(frame_filename, frame)
    print(f"保存帧 {current_frame} 到 {frame_filename}")

    current_frame += 1

cap.release()
print("帧提取完成！")
