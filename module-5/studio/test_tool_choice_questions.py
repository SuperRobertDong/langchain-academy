"""
测试 tool_choice 的两个问题：
1. 多个tools时，tool_choice是"保底"还是"强制选择"？
2. 无法抽取数据时，返回什么？
"""
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from trustcall import create_extractor

model = ChatTongyi(model="qwen-plus", model_kwargs={"temperature": 0}, streaming=False)

class UserProfile(BaseModel):
    user_name: str = Field(description="The user's preferred name")
    interests: list[str] = Field(description="A list of the user's interests")

class ProductInfo(BaseModel):
    product_name: str = Field(description="Product name")
    price: float = Field(description="Product price")

print("=" * 60)
print("问题1: tool_choice 是'保底'还是'强制选择'？")
print("=" * 60)
print("\n注意：通义千问（ChatTongyi）的 tool_choice 只支持 'auto' 或 'none'")
print("不能直接指定工具名称，这是 API 的限制\n")

# 测试：单个工具 + tool_choice="auto"
print("测试场景1: 单个工具 + tool_choice='auto'")
extractor_single = create_extractor(
    model,
    tools=[UserProfile],  # 只有1个工具
    tool_choice="auto"  # 让模型自动选择（因为只有一个，肯定会选它）
)

conversation1 = [
    HumanMessage(content="Hi, I'm Lance."),
    HumanMessage(content="I like biking.")
]

result1 = extractor_single.invoke({
    "messages": [SystemMessage(content="Extract user profile from conversation")] + conversation1
})

print(f"提取到的数据: {result1.get('responses', [])}")

# 测试：多个工具 + tool_choice="auto"
print("\n测试场景2: 多个工具 + tool_choice='auto'")
extractor_multi = create_extractor(
    model,
    tools=[UserProfile, ProductInfo],  # 2个工具
    tool_choice="auto"  # 模型自动选择使用哪个
)

conversation2 = [
    HumanMessage(content="Hi, I'm Lance."),
    HumanMessage(content="I like biking. Also, I bought a bike for $500.")
]

result2 = extractor_multi.invoke({
    "messages": [SystemMessage(content="Extract information from conversation")] + conversation2
})

print(f"提取到的数据: {result2.get('responses', [])}")
for r in result2.get('responses', []):
    print(r.model_dump())

print("\n结论：")
print("- tool_choice='auto'：模型会从 tools 中选择合适的工具使用")
print("- 如果只有一个工具，通常会选择它")
print("- 如果有多个工具，模型会根据对话内容选择最合适的")
print("- 这是'自动选择'，不是'强制选择'\n")

print("=" * 60)
print("问题2: 无法抽取数据时，返回什么？")
print("=" * 60)

# 使用单个工具的 extractor
extractor_single = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="auto"
)

# 测试场景：对话中完全没有用户信息
empty_conversation = [
    HumanMessage(content="The weather is nice today.")
]

result_empty = extractor_single.invoke({
    "messages": [SystemMessage(content="Extract user profile from conversation")] + empty_conversation
})

print("\n对话内容：'The weather is nice today.'（无用户信息）")
print(f"\n结果：")
print(f"提取到的数据: {result_empty.get('responses', [])}")

if result_empty.get('responses'):
    response = result_empty['responses'][0]
    print(f"\n详细内容：")
    print(f"- user_name: {response.get('user_name', 'NOT_FOUND')}")
    print(f"- interests: {response.get('interests', 'NOT_FOUND')}")
else:
    print("\n没有提取到数据（可能是模型选择不调用工具，或者返回了空结果）")

print("\n结论：")
print("- tool_choice='auto' 时，如果无法抽取数据，模型可能：")
print("  1. 仍会调用工具，但返回空值（user_name='', interests=[]）")
print("  2. 或者不调用工具（取决于模型判断）")
print("- 建议：如果只有一个工具且需要保证结构化输出，可以用 tool_choice='auto'")
print("  并确保系统提示足够明确，让模型知道必须提取信息")

