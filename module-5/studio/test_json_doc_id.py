"""
测试 json_doc_id 的工作机制
回答三个问题：
1. json_doc_id 是从哪里生成的
2. 老的 collection 的 json_doc_id 是否不变
3. store.put 插入已有的 key 是否就是 update
"""
import os
import uuid
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from trustcall import create_extractor
from langgraph.store.memory import InMemoryStore

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

# 创建一个 store 来测试
store = InMemoryStore()
namespace = ("test", "user1")

print("=" * 80)
print("问题1: json_doc_id 是从哪里生成的？")
print("=" * 80)

# 第一次调用：没有 existing
print("\n第一次调用（没有 existing）:")
result1 = extractor.invoke({
    "messages": [SystemMessage(content="Extract memories"), HumanMessage(content="I like biking.")]
})

print(f"response_metadata: {result1.get('response_metadata', [])}")
for i, rmeta in enumerate(result1.get('response_metadata', [])):
    json_doc_id = rmeta.get("json_doc_id")
    print(f"  响应 {i}: json_doc_id = {json_doc_id}")
    if json_doc_id is None:
        print(f"    → 这是新创建的，json_doc_id 为 None")

# 保存到 store
for r, rmeta in zip(result1["responses"], result1["response_metadata"]):
    doc_id = rmeta.get("json_doc_id", str(uuid.uuid4()))
    store.put(namespace, doc_id, r.model_dump(mode="json"))
    print(f"  保存到 store: key={doc_id}, value={r.model_dump()}")

print("\n答案1:")
print("- 如果模型决定更新现有对象，json_doc_id 来自于 existing_memories 中的 ID")
print("- 如果模型创建新对象，json_doc_id 为 None，代码中会用 uuid.uuid4() 生成新 ID")

print("\n" + "=" * 80)
print("问题2: 老的 collection 的 json_doc_id 是否不变？")
print("=" * 80)

# 从 store 读取现有数据
existing_items = store.search(namespace)
print(f"\n从 store 读取到的现有记忆:")
for item in existing_items:
    print(f"  key: {item.key}, value: {item.value}")

# 准备 existing_memories（使用 store 中的 key）
existing_memories = [
    (item.key, "Memory", item.value) for item in existing_items
]
print(f"\nexisting_memories: {existing_memories}")

# 第二次调用：有 existing
print("\n第二次调用（有 existing，使用原来的 key）:")
result2 = extractor.invoke({
    "messages": [SystemMessage(content="Update memories"), HumanMessage(content="I also like swimming.")],
    "existing": existing_memories
})

print(f"response_metadata: {result2.get('response_metadata', [])}")
for i, rmeta in enumerate(result2.get('response_metadata', [])):
    json_doc_id = rmeta.get("json_doc_id")
    print(f"  响应 {i}: json_doc_id = {json_doc_id}")
    if json_doc_id:
        print(f"    → 这个 ID 与 existing_memories 中的 ID 相同吗？")
        print(f"    → existing_memories IDs: {[e[0] for e in existing_memories]}")

print("\n答案2:")
print("- 如果模型决定更新，json_doc_id 会使用 existing_memories 中的 ID（原来的 key）")
print("- 如果模型创建新对象，json_doc_id 为 None，会生成新的 UUID")
print("- 所以老的 collection 的 json_doc_id 在更新时保持不变")

print("\n" + "=" * 80)
print("问题3: store.put 插入已有的 key 是否就是 update？")
print("=" * 80)

# 测试 store.put 的行为
test_key = "test_key_123"
test_value1 = {"content": "Original memory"}
test_value2 = {"content": "Updated memory"}

print(f"\n测试 store.put 的行为:")
print(f"1. 第一次 put: key={test_key}, value={test_value1}")
store.put(namespace, test_key, test_value1)
retrieved1 = store.get(namespace, test_key)
print(f"   读取结果: {retrieved1.value if retrieved1 else 'None'}")

print(f"\n2. 第二次 put（相同的 key）: key={test_key}, value={test_value2}")
store.put(namespace, test_key, test_value2)
retrieved2 = store.get(namespace, test_key)
print(f"   读取结果: {retrieved2.value if retrieved2 else 'None'}")

print("\n答案3:")
print("- store.put 如果使用已有的 key，会覆盖（update）原有的值")
print("- 这就是为什么可以使用 rmeta.get('json_doc_id', str(uuid.uuid4()))：")
print("  * 如果 json_doc_id 存在（更新），使用原来的 key → 覆盖")
print("  * 如果 json_doc_id 不存在（新建），生成新 UUID → 插入新记录")

