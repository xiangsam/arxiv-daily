import requests
import json
import time
from typing import Optional

GLOBAL_LLM = None

class LLM:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.max_retries = 3
        self.wait_time = 0.2 # 等待时间（秒）
        self.model_name = model_name
        self.base_url = base_url + '/v1/chat/completions'
        self._api_key = api_key
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": 'Bearer ' + api_key,
        }


    def generate(self, messages: list[dict]) -> Optional[str]:
        data = {
            'model': self.model_name,
            'apiKey': self._api_key,
            "messages": messages,
            "temperature": 0.0
        }
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = requests.post(self.base_url, headers=self._headers, data=json.dumps(data))
                response.raise_for_status()  # 如果请求失败，将抛出HTTPError异常
                response_data = response.json()
                assistant_message = response_data.get('choices', [{}])[0].get('message', {}).get('content')
                return assistant_message
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print(f"遇到429错误，等待{self.wait_time}秒后重试...")
                    time.sleep(self.wait_time)
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        print("达到最大重试次数，退出对话。")
                        return None
                else:
                    print(f"请求失败: {e}")
                    return None
        return None

def set_global_llm(api_key: str, base_url: str, model: str):
    global GLOBAL_LLM
    GLOBAL_LLM = LLM(api_key=api_key, base_url=base_url, model_name=model)

def get_llm() -> LLM:
    if GLOBAL_LLM is None:
        raise ValueError("请先调用set_global_llm函数初始化全局LLM对象")
    return GLOBAL_LLM