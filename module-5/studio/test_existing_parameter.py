"""
测试 trustcall 的 existing 参数是如何工作的
验证：existing 是被添加到 prompt 中，还是 trustcall 内部处理的？
"""
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from trustcall import create_extractor

model = ChatTongyi(model="qwen-plus", model_kwargs={"temperature": 0}, streaming=False)

class Memory(BaseModel):
    content: str = Field(description="The main content of the memory.")

# 创建 extractor
extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="auto",
    enable_inserts=True
)

# 创建回调来拦截实际发送给模型的消息
class PromptInterceptor(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        print("=" * 80)
        print("实际发送给模型的消息:")
        print("=" * 80)
        
        for msg in messages[0] if messages and isinstance(messages[0], list) else messages:
            if hasattr(msg, 'content'):
                print(f"\n消息类型: {type(msg).__name__}")
                print(f"消息内容: {msg.content}")
                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                    print(f"额外参数: {msg.additional_kwargs}")
        
        if 'invocation_params' in kwargs:
            params = kwargs['invocation_params']
            print(f"\n调用参数:")
            print(f"  tools: {params.get('tools', [])}")
        print("=" * 80)

# 第一次调用：没有 existing
print("\n【测试1】没有 existing 参数")
print("-" * 80)
interceptor = PromptInterceptor()
result1 = extractor.invoke(
    {"messages": [SystemMessage(content="Extract memories"), HumanMessage(content="I like biking.")]},
    config=RunnableConfig(callbacks=[interceptor])
)
print(f"\n结果: {result1.get('responses', [])}")

# 第二次调用：有 existing
print("\n\n【测试2】有 existing 参数")
print("-" * 80)
existing_memories = [
    ("0", "Memory", {"content": "User likes biking."})
]
interceptor2 = PromptInterceptor()
result2 = extractor.invoke(
    {
        "messages": [SystemMessage(content="Update memories"), HumanMessage(content="I also like swimming.")],
        "existing": existing_memories
    },
    config=RunnableConfig(callbacks=[interceptor2])
)
print(f"\n结果: {result2.get('responses', [])}")
print(f"响应元数据: {result2.get('response_metadata', [])}")

print("\n\n【结论】")
print("=" * 80)
print("比较两次调用的 prompt：")
print("- 如果 existing 的内容出现在 prompt 中 → existing 被添加到 prompt")
print("- 如果两次 prompt 相同，但结果不同 → trustcall 内部处理合并")
print("- 查看 response_metadata 中的 json_doc_id 可以知道哪些是更新的，哪些是新增的")

