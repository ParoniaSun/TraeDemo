import os
import time
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
from src.translation.deepseek_api import DeepSeekAPI

logger = logging.getLogger(__name__)

# 确保日志记录器已配置
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

class Translator:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api = DeepSeekAPI(self.api_key)
        self.custom_terms: Dict[str, str] = {}
        self.quota_limit = 1000000
        self.quota_used = 0
        self.timeout = 30  # 设置超时时间为30秒
        self.progress_callback = None
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试间隔（秒）

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh') -> Optional[str]:
        """翻译文本"""
        if not text.strip():
            logger.warning("收到空文本，跳过翻译")
            return ""

        try:
            # 检查API密钥是否存在
            if not self.api_key:
                raise ValueError("API密钥未设置，请检查环境变量配置")

            # 应用自定义术语替换
            for term, translation in self.custom_terms.items():
                text = text.replace(term, translation)

            # 重试机制
            for attempt in range(self.max_retries):
                try:
                    result = self.api.translate(
                        text=text,
                        source_language=source_lang,
                        target_language=target_lang
                    )
                    
                    if result:
                        self.quota_used += len(text)
                        logger.info(f"翻译成功: {len(text)} 字符")
                        if self.progress_callback:
                            self.progress_callback(1.0)  # 完成进度
                        return result

                except Exception as e:
                    logger.warning(f"翻译尝试 {attempt + 1}/{self.max_retries} 失败: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise

            return None

        except ValueError as e:
            logger.error(f"配置错误: {str(e)}")
            if self.progress_callback:
                self.progress_callback(-1)
            return None
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            if self.progress_callback:
                self.progress_callback(-1)
            return None

    def load_terms(self, terms_file: str) -> bool:
        """加载专业术语词典"""
        try:
            if not os.path.exists(terms_file):
                logger.error(f"术语文件不存在: {terms_file}")
                return False

            with open(terms_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        term, trans = line.strip().split(':', 1)
                        self.custom_terms[term.strip()] = trans.strip()

            logger.info(f"成功加载术语: {len(self.custom_terms)} 条")
            return True

        except Exception as e:
            logger.error(f"加载术语失败: {str(e)}")
            return False

    def get_quota_status(self) -> Dict[str, int]:
        """获取API配额使用状态"""
        return {
            'limit': self.quota_limit,
            'used': self.quota_used,
            'remaining': self.quota_limit - self.quota_used
        }

    def add_term(self, term: str, translation: str):
        """添加自定义术语"""
        self.custom_terms[term] = translation
        logger.info(f"添加术语: {term} -> {translation}")

    def remove_term(self, term: str):
        """删除自定义术语"""
        if term in self.custom_terms:
            del self.custom_terms[term]
            logger.info(f"删除术语: {term}")