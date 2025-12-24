import os
import json
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_core.messages import SystemMessage
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b

tools = [add, multiply, divide]

# Define LLM with bound tools
llm = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0}  # 通过 model_kwargs 设置温度
)
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="You are a helpful assistant tasked with writing performing arithmetic on a set of inputs.")

# Node
def assistant(state: MessagesState):
    print(state["messages"])
    print('====================')
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")
graph = builder.compile()

# Compile graph
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "123"}}
result = graph.invoke({"messages": [HumanMessage(content="add 3 and 5. Multiple the output by 2. Devide the output by 5")]},
 config)
# print(f"the final result is: ====================")
# for m in result["messages"]:
#     m.pretty_print()

# print(f"this is the step2 of the test: ====================")
# messages = [HumanMessage(content="mutiple that by 2", name="Robert")]
# result = graph.invoke({"messages": messages}, config)
# print(f"the final result is: ====================")
# for m in result["messages"]:
#     m.pretty_print()