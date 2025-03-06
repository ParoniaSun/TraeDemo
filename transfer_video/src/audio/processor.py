import os
from typing import Optional
import whisper
from edge_tts import Communicate
from loguru import logger
from pydub import AudioSegment

class AudioProcessor:
    def __init__(self):
        try:
            # 检查 whisper 模块是否正确安装
            if not whisper.__version__:
                raise ImportError("Whisper 模块未正确安装，请检查依赖项")

            # 尝试加载模型
            try:
                self.model = whisper.load_model("base")
            except AttributeError:
                logger.error("Whisper模块缺少load_model方法，可能是版本不兼容")
                raise ImportError("请安装正确版本的Whisper模块")
            except Exception as e:
                logger.error(f"加载Whisper模型失败: {str(e)}")
                raise

            if not self.model:
                raise ValueError("Whisper 模型加载失败，返回为空")

            # 验证模型是否可用
            if not hasattr(self.model, 'transcribe'):
                raise AttributeError("加载的模型缺少必要的 transcribe 方法")

            logger.info("成功加载 Whisper 模型")

        except ImportError as e:
            logger.error(f"Whisper 模块导入失败: {str(e)}")
            raise Exception("请确保已正确安装 Whisper 及其依赖项")
        except (ValueError, AttributeError) as e:
            logger.error(f"Whisper 模型加载失败: {str(e)}")
            raise Exception("模型文件可能损坏或不完整，请重新安装")
        except Exception as e:
            logger.error(f"初始化语音识别模型时发生未知错误: {str(e)}")
            raise Exception("初始化语音识别模型失败，请检查系统环境和权限")
        
        self.voice = "zh-CN-XiaoxiaoNeural"
        self.rate = "+0%"
        self.volume = "+0%"

    async def speech_to_text(self, audio_path: str) -> Optional[str]:
        """将音频转换为文字"""
        try:
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return None

            # 首先将语音转换为英文文本
            result = self.model.transcribe(audio_path)
            english_text = result["text"]
            logger.info(f"音频转英文文字成功: {len(english_text)} 字符")

            # 初始化翻译器并将英文翻译为中文
            from src.translation.translator import Translator
            translator = Translator()
            chinese_text = translator.translate(english_text, source_lang='en', target_lang='zh')
            
            if not chinese_text:
                logger.error("英文转中文翻译失败")
                return None

            logger.info(f"英文翻译为中文成功: {len(chinese_text)} 字符")
            # print('------------->', chinese_text)
            return chinese_text

        except Exception as e:
            logger.error(f"音频转文字失败: {str(e)}")
            return None

    async def text_to_speech(self, text: str, output_path: str) -> bool:
        """将文字转换为语音"""
        # print('0---------->', output_path)
        try:
            if not text or not text.strip():
                logger.error("输入文本为空")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")

            # 创建通信对象
            communicate = Communicate(
                text,
                self.voice,
                rate=self.rate,
                volume=self.volume
            )

            # 保存音频文件
            try:
                logger.info(f"开始生成语音文件: {output_path}")
                logger.info(f"使用语音: {self.voice}, 语速: {self.rate}, 音量: {self.volume}")
                
                # 删除可能存在的旧文件
                if os.path.exists(output_path):
                    os.remove(output_path)
                    logger.info(f"删除已存在的音频文件: {output_path}")
                
                # 保存音频
                output_path_mp3 = output_path.replace('wav','mp3')
                await communicate.save(output_path_mp3)
                sound = AudioSegment.from_mp3(output_path_mp3)
                sound.export(output_path, format="wav")
                logger.info(f"mp3转wav成功，文件大小: {os.path.getsize(output_path)} 字节")
                os.remove(output_path_mp3)
                
                # 验证文件是否成功生成
                if not os.path.exists(output_path):
                    raise FileNotFoundError("语音文件生成失败，文件不存在")
                
                file_size = os.path.getsize(output_path)
                if file_size == 0:
                    raise ValueError("生成的音频文件大小为0字节")
                    
                logger.info(f"文字转语音成功，文件大小: {file_size} 字节")
                return True
            except Exception as e:
                logger.error(f"保存语音文件失败: {str(e)}")
                # 尝试获取更详细的错误信息
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                return False

        except Exception as e:
            logger.error(f"文字转语音失败: {str(e)}，文本长度: {len(text)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def set_voice(self, voice: str):
        """设置TTS声音"""
        self.voice = voice

    def set_rate(self, rate: str):
        """设置语速"""
        self.rate = rate

    def set_volume(self, volume: str):
        """设置音量"""
        self.volume = volume