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

from typing import TypedDict

class UserProfile(TypedDict):
    """User profile schema with typed fields"""
    user_name: str  # The user's preferred name
    interests: list[str]  # A list of the user's interests

user_profile: UserProfile = {
    "user_name": "John Doe",
    "interests": ["biking", "technology", "coffee"]
}

# import uuid 
from langgraph.store.memory import InMemoryStore
# from langchain_core.messages import HumanMessage

# in_memory_store = InMemoryStore()

# user_id = "1"
# namespace_for_memory = (user_id, "memories")
# key = str(uuid.uuid4())
# value = user_profile

# in_memory_store.put(namespace_for_memory, key, user_profile)
# memories = in_memory_store.search(namespace_for_memory)
# print(memories[0].value)

# memory = in_memory_store.get(namespace_for_memory, key)
# print(memory.value)

# model_with_structure = model.with_structured_output(UserProfile)
# structured_output = model_with_structure.invoke([HumanMessage(content="My name is Lance, I like to bike and eat at bakeries.")])
# print(structured_output)

# import uuid
# from langgraph.store.memory import InMemoryStore

# in_memory_store = InMemoryStore()

# user_id = "1"
# namespace_for_memory = (user_id, "memories")
# key = str(uuid.uuid4())
# value = {"food_preference": "I like pizza"}

# in_memory_store.put(namespace_for_memory, key, value)
# memories = in_memory_store.search(namespace_for_memory)
# print(memories[0].value)

# memory = in_memory_store.get(namespace_for_memory, key)
# print(memory.value)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.base import BaseStore

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. 
If you have memory for this user, use it to personalize your responses.
Here is the memory (it may be empty): {memory}"""

# Create new memory from the chat history and any existing memory
CREATE_MEMORY_INSTRUCTION = """"You are collecting information about the user to personalize your responses.

CURRENT USER INFORMATION:
{memory}

INSTRUCTIONS:
1. Review the chat history below carefully
2. Identify new information about the user, such as:
   - Personal details (name, location)
   - Preferences (likes, dislikes)
   - Interests and hobbies
   - Past experiences
   - Goals or future plans
3. Merge any new information with existing memory
4. Format the memory as a clear, bulleted list
5. If new information conflicts with existing memory, keep the most recent version

Remember: Only include factual information directly stated by the user. Do not make assumptions or inferences.

Based on the chat history below, please update the user information:"""

def call_model(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memory from the store and use it to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memory", user_id)
    key = "user_memory"
    existing_memory = store.get(namespace, key)

    # Extract the actual memory content if it exists and add a prefix
    if existing_memory:
        # Value is a dictionary with a memory key
        existing_memory_content = existing_memory.value.get('memory')
    else:
        existing_memory_content = "No existing memory found."

    # Format the memory in the system prompt
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=existing_memory_content)
    
    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve existing memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")
        
    # Extract the memory
    if existing_memory:
        existing_memory_content = existing_memory.value.get('memory')
    else:
        existing_memory_content = "No existing memory found."

    # Format the memory in the system prompt
    system_msg = CREATE_MEMORY_INSTRUCTION.format(memory=existing_memory_content)
    # new_memory = model.invoke([SystemMessage(content=system_msg)]+state['messages'])
    model_with_structure = model.with_structured_output(UserProfile)
    structured_output = model_with_structure.invoke([SystemMessage(content=system_msg)]+state['messages'])

    # Overwrite the existing memory in the store 
    key = "user_memory"

    # Write value as a dictionary with a memory key
    store.put(namespace, key, {"memory": structured_output})

builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("write_memory", write_memory)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", "write_memory")
builder.add_edge("write_memory", END)

memory = MemorySaver()
across_thread_memory = InMemoryStore()
graph = builder.compile(checkpointer=memory, store=across_thread_memory)

user_id = "1"
config = {"configurable": {"user_id": user_id, "thread_id": "1"}}

input_messages = [HumanMessage(content="Hi, I am Robert")]
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

input_messages = [HumanMessage(content="I like to bike around San Francisco and eat bakeries.")]
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

state = graph.get_state(config).values
for m in state["messages"]:
    m.pretty_print()

namespace = ("memory", user_id)
existing_memory = across_thread_memory.get(namespace, "user_memory")
print(existing_memory.dict())

config = {"configurable": {"user_id": user_id, "thread_id": "2"}}

input_messages = [HumanMessage(content="Hi! Where would you recommend that I go biking?")]
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

existing_memory = across_thread_memory.get(namespace, "user_memory")
print(existing_memory.dict())