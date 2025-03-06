import requests
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 确保日志记录器已配置
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

class DeepSeekAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"  # 更新为chat completions接口
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        # 设置请求超时和重试机制
        self.session.timeout = (5, 30)  # 连接超时5秒，读取超时30秒
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def translate(self, text: str, source_language: str = 'en', target_language: str = 'zh') -> Optional[str]:
        """调用DeepSeek API进行文本翻译

        Args:
            text: 要翻译的文本
            source_language: 源语言代码
            target_language: 目标语言代码

        Returns:
            翻译后的文本，如果翻译失败则返回None
        """
        try:
            # 构建翻译提示
            prompt = f"Please translate the following text from {source_language} to {target_language}:\n{text}"
            
            response = self.session.post(
                self.base_url,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                translation = result["choices"][0]["message"]["content"].strip()
                return translation
            else:
                logger.error(f"翻译API返回格式错误: {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"翻译API请求失败: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"翻译API返回数据解析失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"翻译过程发生未知错误: {str(e)}")
            return None