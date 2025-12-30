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

model = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0},  # 通过 model_kwargs 设置温度
    streaming=True
)

from pydantic import BaseModel, Field

class Memory(BaseModel):
    content: str = Field(description="The main content of the memory. For example: User expressed interest in learning about French.")

class MemoryCollection(BaseModel):
    memories: list[Memory] = Field(description="A list of memories about the user.")

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

model_with_structure = model.with_structured_output(MemoryCollection)

memory_collection = model_with_structure.invoke([HumanMessage(content="My name is Lance. I like to bike.")])
for m in memory_collection.memories:
    print(m.content)

from trustcall import create_extractor

# Create the extractor
# 注意：通义千问可能对 enable_inserts 和 existing 参数的支持有限
# 如果继续报错，可以尝试关闭 enable_inserts 或使用不同的模型
trustcall_extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="auto",  # 通义千问只支持 "auto" 或 "none"
    enable_inserts=True,
)

instruction = """Extract memories from the following conversation:"""
conversation = [HumanMessage(content="Hi, I'm Lance."), 
                AIMessage(content="Nice to meet you, Lance."), 
                HumanMessage(content="This morning I had a nice bike ride in San Francisco.")]

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=instruction)] + conversation})
for m in result.get('responses', []):
    print(m.model_dump_json())

print("*" * 60)

updated_conversation = [AIMessage(content="That's great, did you do after?"), 
                        HumanMessage(content="I went to Tartine and ate a croissant."),                        
                        AIMessage(content="What else is on your mind?"),
                        HumanMessage(content="I was thinking about my Japan, and going back this winter!"),]

# Update the instruction
system_msg = """Update existing memories and create new ones based on the following conversation:"""

# We'll save existing memories, giving them an ID, key (tool name), and value
tool_name = "Memory"
existing_memories = [(str(i), tool_name, memory.model_dump()) for i, memory in enumerate(result["responses"])] if result["responses"] else None

# 添加 recursion_limit 配置并确保消息格式正确
from langchain_core.runnables import RunnableConfig

# 如果 existing_memories 为空或 None，则不传递 existing 参数
invoke_params = {
    "messages": [SystemMessage(content=system_msg)] + updated_conversation
}
if existing_memories:
    invoke_params["existing"] = existing_memories

try:
    result = trustcall_extractor.invoke(
        invoke_params,
        config=RunnableConfig(recursion_limit=100)  # 大幅增加递归限制
    )
except Exception as e:
    print(f"错误: {e}")
    print("\n尝试使用不启用 enable_inserts 的版本...")
    
    # 备选方案：不使用 enable_inserts
    extractor_no_inserts = create_extractor(
        model,
        tools=[Memory],
        tool_choice="auto",
        enable_inserts=False  # 关闭插入功能
    )
    
    # 只提取新记忆，不更新现有记忆
    result = extractor_no_inserts.invoke({
        "messages": [SystemMessage(content="Extract new memories from the conversation:")] + updated_conversation
    })
    print("使用 enable_inserts=False 成功提取新记忆")

for m in result["messages"]:
    m.pretty_print()

    



