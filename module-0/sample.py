import os
import getpass
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# print(os.environ.get("OPENAI_API_KEY"))

# ============================================
# 使用 OpenAI 模型
# ============================================
# from langchain_openai import ChatOpenAI
# gpt4o_chat = ChatOpenAI(model="gpt-4o", temperature=0)
# gpt35_chat = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

# ============================================
# 使用阿里千问模型 - 方式1：使用 ChatTongyi（推荐）
# ============================================
# 注意：需要先安装 dashscope: pip install dashscope
from langchain_community.chat_models import ChatTongyi

# 设置千问 API Key（DASHSCOPE_API_KEY）
print(os.environ.get("DASHSCOPE_API_KEY"))

# 初始化千问模型
# 可用的模型：qwen-turbo, qwen-plus, qwen-max, qwen-max-longcontext 等
# 注意：ChatTongyi 会自动从环境变量 DASHSCOPE_API_KEY 读取
# 温度参数需要通过 model_kwargs 传递
qwen_chat = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0}  # 通过 model_kwargs 设置温度
)

from langchain_core.messages import HumanMessage
msg = HumanMessage(content="Hello world", name="Lance")

# Message list
messages = [msg]

# Invoke the model with a list of messages 
qwen_chat.invoke(messages)

# ============================================
# 使用阿里千问模型 - 方式2：使用 ChatOpenAI（兼容模式）
# ============================================
# 注意：这种方式需要设置 base_url 为千问的兼容接口
# qwen_chat_compatible = ChatOpenAI(
#     model="qwen-plus",
#     temperature=0,
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     api_key=os.environ.get("DASHSCOPE_API_KEY")
# )

from langchain_community.tools.tavily_search import TavilySearchResults
search = TavilySearchResults(max_results=2)
result = search.invoke("What is the capital of France?")
print(result)