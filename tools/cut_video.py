from moviepy.video.io.VideoFileClip import VideoFileClip

def cut_video(input_path, output_path, start_time, end_time):
    """
    从输入视频中截取从 start_time 到 end_time 时间段的视频，并保存到 output_path。
    
    参数:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        start_time: 截取起始时间（单位：秒）
        end_time: 截取结束时间（单位：秒）
    """
    clip = VideoFileClip(input_path)
    
    try:
        # 尝试使用 subclip 方法
        new_clip = clip.subclip(start_time, end_time)
    except AttributeError:
        # 如果不存在 subclip 方法，尝试使用 subclipped 方法（部分版本可能命名为 subclipped）
        new_clip = clip.subclipped(start_time, end_time)
    
    new_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    input_path = r"E:\A_Work\学术\FreeAD_机器人端到端自动驾驶\可视化结果\vis_VAD.mp4"
    output_path = "cuted_video.mp4"
    start = 60*1 + 56  # 1 分钟 56 秒
    end = 60*2 + 7     # 2 分钟 7 秒

    cut_video(input_path, output_path, start, end)
