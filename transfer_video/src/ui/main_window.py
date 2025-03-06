import os
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QSlider, QProgressDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from loguru import logger
import asyncio

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频翻译工具")
        self.resize(1200, 800)
        
        # 初始化媒体播放器
        self.media_player = QMediaPlayer()
        self.video_widget = None
        # 创建并设置音频输出
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)  # 设置默认音量为最大
        self.media_player.setAudioOutput(self.audio_output)
        
        # 设置媒体播放器错误处理
        self.media_player.errorOccurred.connect(self.handle_media_error)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # 初始化定时器用于更新进度
        self.timer = QTimer()
        self.timer.setInterval(1000)  # 每秒更新一次
        self.timer.timeout.connect(self.update_position)
        
        self.setup_ui()

    def handle_media_error(self, error, error_string):
        """处理媒体播放器错误"""
        error_message = f"视频加载失败: {error_string}"
        if error == QMediaPlayer.Error.ResourceError:
            error_message = "无法访问视频文件，请检查文件权限或是否被占用"
        elif error == QMediaPlayer.Error.FormatError:
            error_message = "不支持的视频格式，请使用其他格式的视频文件"
        elif error == QMediaPlayer.Error.NetworkError:
            error_message = "网络错误，请检查网络连接"
        QMessageBox.critical(self, "错误", error_message)

    def handle_media_status(self, status):
        """处理媒体状态变化"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # 视频加载完成后启动定时器
            self.timer.start()
            self.position_slider.setEnabled(True)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            QMessageBox.warning(self, "警告", "无效的视频文件，请确保文件格式正确且未被损坏")
            self.position_slider.setEnabled(False)
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            self.position_slider.setEnabled(False)

    def setup_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        # 导入视频按钮
        import_btn = QPushButton("导入视频")
        import_btn.clicked.connect(self.import_video)
        toolbar_layout.addWidget(import_btn)
        
        # 开始翻译按钮
        translate_btn = QPushButton("开始翻译")
        translate_btn.clicked.connect(lambda: asyncio.run(self.start_translation()))
        toolbar_layout.addWidget(translate_btn)
        
        # 导出视频按钮
        export_btn = QPushButton("导出视频")
        export_btn.clicked.connect(self.export_video)
        toolbar_layout.addWidget(export_btn)
        
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar)

        # 视频预览窗口
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #2c2c2c;")
        self.media_player.setVideoOutput(self.video_widget)
        main_layout.addWidget(self.video_widget, 1)
        
        # 播放控制区域
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # 播放/暂停按钮
        play_btn = QPushButton("播放/暂停")
        play_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(play_btn)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量")
        volume_label.setStyleSheet("color: white;")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        control_layout.addLayout(volume_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white; min-width: 60px;")
        progress_layout.addWidget(self.current_time_label)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setEnabled(False)
        self.position_slider.sliderMoved.connect(self.set_position)
        progress_layout.addWidget(self.position_slider)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("color: white; min-width: 60px;")
        progress_layout.addWidget(self.duration_label)
        
        control_layout.addLayout(progress_layout)
        main_layout.addWidget(control_panel)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QWidget {
                background-color: #1a1a1a;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #B0BEC5;
                color: #78909C;
            }
        """)

    def import_video(self):
        """导入视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "Video Files (*.mp4 *.avi *.mov);;All Files (*)"
        )
        if file_path:
            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"视频文件不存在: {file_path}")

                # 确保视频输出设备已设置
                if not self.video_widget:
                    self.video_widget = QVideoWidget()
                    self.video_widget.setStyleSheet("background-color: #2c2c2c;")
                
                # 重置媒体播放器
                self.media_player.stop()
                self.media_player.setVideoOutput(self.video_widget)
                
                # 设置视频源
                self.media_player.setSource(QUrl.fromLocalFile(file_path))
                self.position_slider.setEnabled(True)
                
            except FileNotFoundError as e:
                QMessageBox.critical(self, "错误", str(e))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"视频加载失败: {str(e)}\n请确保文件格式正确且未被损坏。")

    async def start_translation(self):
        """开始翻译处理"""
        try:
            # 获取当前视频文件路径
            video_path = self.media_player.source().toString().replace('file://', '')
            if not video_path:
                QMessageBox.warning(self, "警告", "请先导入视频文件")
                return

            # 显示进度对话框
            progress = QProgressDialog("正在处理视频...", "取消", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            
            # 初始化处理器
            from src.video.processor import VideoProcessor
            from src.audio.processor import AudioProcessor
            from src.translation.translator import Translator
            
            video_processor = VideoProcessor()
            audio_processor = AudioProcessor()
            translator = Translator()
            
            # 加载视频
            if not video_processor.load_video(video_path):
                raise Exception("视频加载失败")
            
            # 提取音频
            audio_path = os.path.splitext(video_path)[0] + "_audio.wav"
            if not video_processor.extract_audio(audio_path):
                raise Exception("音频提取失败")
            progress.setValue(20)
            
            # 语音识别
            text = await audio_processor.speech_to_text(audio_path)
            if not text:
                raise Exception("语音识别失败")
            progress.setValue(40)
            
            # 翻译文本
            translated_text = translator.translate(text)
            if not translated_text:
                raise Exception("翻译失败")
            progress.setValue(60)
            
            # 语音合成
            translated_audio_path = os.path.splitext(video_path)[0] + "_translated_audio.wav"
            if not await audio_processor.text_to_speech(translated_text, translated_audio_path):
                raise Exception("语音合成失败")
            progress.setValue(80)
            
            # 合成最终视频
            output_video_path = os.path.splitext(video_path)[0] + "_translated.mp4"
            subtitles = [{
                'start_time': '00:00',
                'end_time': self.format_time(self.media_player.duration()),
                'text': translated_text
            }]
            
            if not video_processor.export_video(video_path, output_video_path, subtitles):
                raise Exception("视频合成失败")
            progress.setValue(100)
            
            QMessageBox.information(self, "提示", "视频翻译完成")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"视频处理失败: {str(e)}")

    def export_video(self):
        """导出翻译后的视频"""
        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出视频",
            "",
            "MP4 Files (*.mp4);;AVI Files (*.avi);;MOV Files (*.mov);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 获取当前视频文件路径
            video_path = self.media_player.source().toString().replace('file://', '')
            if not video_path:
                QMessageBox.warning(self, "警告", "请先导入并翻译视频文件")
                return

            # 导出进度对话框
            progress = QProgressDialog("正在导出视频...", "取消", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            
            def update_progress(value):
                progress.setValue(value)
            
            # 调用视频处理模块进行导出
            from src.video.processor import VideoProcessor
            processor = VideoProcessor()
            processor.set_progress_callback(update_progress)
            
            # 开始导出
            translated_video_path = os.path.splitext(video_path)[0] + "_translated.mp4"
            if os.path.exists(translated_video_path):
                import shutil
                shutil.copy2(translated_video_path, file_path)
                QMessageBox.information(self, "提示", "视频导出成功")
            else:
                QMessageBox.warning(self, "警告", "请先完成视频翻译")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"视频导出失败: {str(e)}")

    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def format_time(self, ms):
        """将毫秒转换为时间格式"""
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def update_position(self):
        """更新视频播放进度"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            # 获取当前播放位置（毫秒）
            position = self.media_player.position()
            duration = self.media_player.duration()
            
            # 更新进度条
            if duration > 0:
                self.position_slider.setValue(int((position / duration) * 100))
            
            # 更新时间标签
            self.current_time_label.setText(self.format_time(position))
            self.duration_label.setText(self.format_time(duration))
        
        # 检查视频是否播放结束
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            self.timer.stop()
            self.position_slider.setValue(0)
            self.current_time_label.setText("00:00")

    def set_position(self, position):
        """设置视频播放位置"""
        # 将百分比位置转换为实际时间位置
        duration = self.media_player.duration()
        position_ms = int((position / 100) * duration)
        self.media_player.setPosition(position_ms)

    def set_volume(self, volume):
        """设置音量"""
        self.audio_output.setVolume(volume / 100)