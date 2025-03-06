import os
from typing import Optional, List, Dict, Callable
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from loguru import logger

class VideoProcessor:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov']
        self.current_video: Optional[VideoFileClip] = None
        self.audio_path: Optional[str] = None
        self.progress_callback: Optional[Callable[[int], None]] = None

    def set_progress_callback(self, callback: Callable[[int], None]):
        """设置进度回调函数"""
        self.progress_callback = callback

    def load_video(self, video_path: str) -> bool:
        """加载视频文件"""
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return False

            file_ext = os.path.splitext(video_path)[1].lower()
            if file_ext not in self.supported_formats:
                logger.error(f"不支持的视频格式: {file_ext}")
                return False

            self.current_video = VideoFileClip(video_path)
            logger.info(f"成功加载视频: {video_path}")
            return True

        except Exception as e:
            logger.error(f"加载视频失败: {str(e)}")
            return False

    def extract_audio(self, output_path: str) -> bool:
        """从视频中提取音频"""
        try:
            if not self.current_video:
                logger.error("没有加载视频文件")
                return False

            if not hasattr(self.current_video, 'audio'):
                logger.error("视频对象不包含音频属性，可能是VideoFileClip初始化失败")
                return False

            audio = self.current_video.audio
            if not audio:
                logger.error("视频文件没有音轨")
                return False

            # 检查输出路径
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")

            # 使用ffmpeg提取音频
            try:
                audio.write_audiofile(output_path, fps=44100, nbytes=2, codec='pcm_s16le')
                self.audio_path = output_path
                logger.info(f"成功提取音频到: {output_path}")
                return True
            except Exception as e:
                logger.error(f"音频写入失败: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"提取音频失败: {str(e)}，类型: {type(e).__name__}")
            return False

    def export_video(self, input_video: str, output_path: str, subtitles: List[Dict[str, str]]) -> bool:
        """导出带字幕的视频

        Args:
            input_video (str): 输入视频路径
            output_path (str): 输出视频路径
            subtitles (list): 字幕列表，每个字幕包含 start_time, end_time, text

        Returns:
            bool: 是否成功
        """
        try:
            # 加载视频
            video = VideoFileClip(input_video)

            # 创建字幕剪辑
            subtitle_clips = []
            for i, subtitle in enumerate(subtitles):
                # 解析时间
                start_time = self._parse_time(subtitle['start_time'])
                end_time = self._parse_time(subtitle['end_time'])

                # 创建字幕
                text_clip = TextClip(
                    subtitle['text'],
                    fontsize=24,
                    color='white',
                    bg_color='rgba(0,0,0,0.5)',
                    font='Arial-Unicode-MS',
                    size=(video.w * 0.8, None),
                    method='label',
                    align='center'
                ).set_duration(end_time - start_time)

                # 设置字幕位置和时间
                text_clip = text_clip.set_position(('center', 'bottom'))
                text_clip = text_clip.set_start(start_time)
                text_clip = text_clip.set_duration(end_time - start_time)

                subtitle_clips.append(text_clip)

                # 更新进度
                if self.progress_callback:
                    progress = (i + 1) / len(subtitles) * 50
                    self.progress_callback(int(progress))

            # 获取翻译后的音频路径
            translated_audio_path = os.path.splitext(input_video)[0] + "_translated_audio.wav"
            if not os.path.exists(translated_audio_path):
                logger.error(f"翻译后的音频文件不存在: {translated_audio_path}")
                return False

            # 检查音频文件大小
            audio_file_size = os.path.getsize(translated_audio_path)
            if audio_file_size == 0:
                logger.error(f"翻译后的音频文件大小为0字节: {translated_audio_path}")
                return False

            logger.info(f"加载翻译后的音频文件: {translated_audio_path}, 大小: {audio_file_size} 字节")

            # 加载翻译后的音频
            try:
                # 直接使用AudioFileClip而不是VideoFileClip来加载音频
                from moviepy.audio.io.AudioFileClip import AudioFileClip
                translated_audio = AudioFileClip(translated_audio_path)

                if not translated_audio:
                    logger.error("无法加载翻译后的音频")
                    return False

                logger.info(f"成功加载翻译后的音频，时长: {translated_audio.duration} 秒")
            except Exception as e:
                logger.error(f"加载翻译后的音频失败: {str(e)}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                return False

            # 合成视频，使用翻译后的音频
            video = video.set_audio(translated_audio)
            final_video = CompositeVideoClip([video] + subtitle_clips, size=video.size)

            # 导出视频
            # 获取视频帧率，如果无法获取则使用默认值
            try:
                video_fps = video.fps
                if not video_fps or video_fps <= 0:
                    video_fps = 24
                    logger.warning(f"无法获取视频帧率，使用默认值: {video_fps}")
                else:
                    logger.info(f"使用原始视频帧率: {video_fps}")
            except Exception as e:
                video_fps = 24
                logger.warning(f"获取视频帧率失败: {str(e)}，使用默认值: {video_fps}")

            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=video_fps,
                verbose=False,
                threads=4,  # 优化性能
                preset='fast',  # 平衡压缩率和速度
                ffmpeg_params=[
                    '-crf', '23',  # 控制画质（18-28，越小质量越高）
                    '-pix_fmt', 'yuv420p'  # 确保兼容性
                ]
            )

            # 清理资源
            video.close()
            translated_audio.close()
            for clip in subtitle_clips:
                clip.close()
            final_video.close()

            if self.progress_callback:
                self.progress_callback(100)

            logger.info(f"成功导出视频到: {output_path}")
            return True

        except Exception as e:
            error_msg = str(e)
            if "ImageMagick" in error_msg:
                logger.error("导出视频失败: ImageMagick未正确安装。请按照以下步骤安装ImageMagick：\n"
                             "1. macOS: 使用brew install imagemagick\n"
                             "2. Linux: 使用apt-get install imagemagick或yum install imagemagick\n"
                             "3. Windows: 从 https://imagemagick.org/script/download.php 下载并安装，"
                             "然后将安装路径添加到系统环境变量")
            else:
                logger.error(f"导出视频失败: {error_msg}")
            return False

    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except Exception as e:
            logger.error(f"解析时间失败: {str(e)}")
            return 0

    def close(self):
        """释放资源"""
        if self.current_video:
            self.current_video.close()
            self.current_video = None
            self.audio_path = None