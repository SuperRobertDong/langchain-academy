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
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver

model = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0}  # 通过 model_kwargs 设置温度
)

class State(MessagesState):
    summary: str

def call_model(state: State):
    summary = state.get("summary", "")
    if summary:
        system_message = f"Summary of conversation earlier: {summary}"
        messages = [SystemMessage(content=system_message)] + state["messages"]
    else:
        messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": response}

def summarize_conversation(state: State):
    summary = state.get("summary", "")
    if summary:
        summary_message = (f"This is summary of the conversation to date: {summary}\n\n" +
            "Extend the summary by taking into account the new messages above:")
    else:
        summary_message = "Create a summary of the conversation above:"

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content,"messages": delete_messages}

def should_continue(state: State):
    messages = state["messages"]
    if len(messages) > 6:
        return "summarize_conversation"
    else:
        return END

builder = StateGraph(State)
builder.add_node("call_model", call_model)
builder.add_node("summarize_conversation", summarize_conversation)
builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", should_continue)
builder.add_edge("summarize_conversation", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "123"}}

result = graph.invoke({"messages": [HumanMessage(content="Hi! I am Robert")]}, 
    config=config)
for m in result["messages"]:
    m.pretty_print()

print("====================================")

result = graph.invoke({"messages": [HumanMessage(content="What's my name?")]}, 
    config=config)
for m in result["messages"]:
    m.pretty_print()

print("====================================")
result = graph.invoke({"messages": [HumanMessage(content="I like the 49ers!")]}, 
    config=config)
for m in result["messages"]:
    m.pretty_print()

print("====================================")
result = graph.invoke({"messages": [HumanMessage(content="I like Nick Bosa, isn't he the highest paid defensive player?")]}, 
    config=config)
for m in result["messages"]:
    m.pretty_print()

print("====================================")
print(graph.get_state(config).values.get("summary","this is no summary yet!"))