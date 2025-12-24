import os
import json
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

# Tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

# LLM with bound tool
llm = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0}  # 通过 model_kwargs 设置温度
)
llm_with_tools = llm.bind_tools([multiply])

# tool_call = llm_with_tools.invoke([HumanMessage(content="What is 2 * 3?")])
# print(tool_call)
# print('====================')
# print(tool_call.additional_kwargs['tool_calls'])



# # Node
def tool_calling_llm(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", END)

# Compile graph
graph = builder.compile()

# message = [HumanMessage(content="Mutiple 2 and 3!")]
# result = graph.invoke({"messages": message})
# for m in result["messages"]:
#     m.pretty_print()