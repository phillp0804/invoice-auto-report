"""從 AI 回傳文字中解析 JSON。

AI 模型有時會把 JSON 包在 Markdown code fence 裡（例如 ```json ... ```），
即使 prompt 明確要求「僅輸出 JSON」也可能發生（實測 Gemini 尤其常見）。
這個純函式負責去除常見的包裝格式，方便呼叫端直接取得解析後的字典。
"""

import json
import re

# 比對整段文字被 ``` 或 ```json 包住的情況，取出中間內容
_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def parse_json_response(text: str) -> dict:
    """解析 AI 回傳的 JSON 字串，容忍常見的 Markdown code fence 包裝。

    Args:
        text: AI 回傳的原始文字。

    Returns:
        解析後的字典。

    Raises:
        json.JSONDecodeError: 去除 code fence 後仍不是合法 JSON。
    """
    stripped = text.strip()
    match = _CODE_FENCE_PATTERN.match(stripped)
    if match:
        stripped = match.group(1).strip()
    return json.loads(stripped)
