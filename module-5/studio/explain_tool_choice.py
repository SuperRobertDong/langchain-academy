import os
import json
from turtle import mode
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from trustcall import create_extractor

model = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0},  # 通过 model_kwargs 设置温度
    streaming=True
)

"""
tool_choice 的作用说明
"""

# ========== 场景1: 不设置 tool_choice 或设为 "auto" ==========
extractor1 = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="auto"  # 或 None
)
"""
结果：模型可以自由选择
- 可能调用 UserProfile 工具返回结构化数据
- 也可能返回普通文本："抱歉，我无法提取用户信息"
- 不确定会得到什么格式的输出
"""

# ========== 场景2: 设置 tool_choice="UserProfile" ==========
extractor2 = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="UserProfile"  # 强制使用这个工具
)
"""
结果：模型必须调用 UserProfile 工具
- 一定会返回符合 UserProfile 结构的数据
- 不会返回普通文本
- 保证输出格式是结构化的
"""

"""
核心区别：

1. tool_choice="auto" 或 None:
   - 模型可以决定是否调用工具
   - 可能返回普通文本回复
   - 输出格式不确定

2. tool_choice="UserProfile":
   - 强制模型必须调用 UserProfile 工具
   - 不会返回普通文本
   - 保证输出符合 UserProfile 的结构定义
   - 这就是"结构化输出"的保证

实际用途：
当你需要确保模型一定返回结构化数据（比如 JSON、Pydantic 模型）时，
就必须设置 tool_choice，否则模型可能"偷懒"返回普通文本。
"""

