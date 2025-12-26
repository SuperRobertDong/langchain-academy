import os
import json
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

import sqlite3
import os

# conn = sqlite3.connect(":memory:")

# 获取项目根目录（从当前文件向上两级目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
db_path = os.path.join(project_root, "state_db", "example.db")

# 确保目录存在（SQLite 不会自动创建目录）
os.makedirs(os.path.dirname(db_path), exist_ok=True)
# SQLite 会自动创建数据库文件（如果不存在）
conn = sqlite3.connect(db_path, check_same_thread=False)

from langgraph.checkpoint.sqlite import SqliteSaver
memory = SqliteSaver(conn)

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END, MessagesState

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

graph = builder.compile(checkpointer=memory)

# ============================================================================
# Checkpoint 管理辅助函数
# ============================================================================

def delete_thread_checkpoint(thread_id: str):
    """
    删除指定线程的所有 checkpoint 记录
    
    Args:
        thread_id: 要删除的线程ID
    """
    memory.delete_thread(thread_id)
    print(f"已删除线程 {thread_id} 的所有 checkpoint 记录")

def list_all_threads():
    """
    列出数据库中所有的线程ID
    
    Returns:
        list: 所有线程ID的列表
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
    all_threads = [row[0] for row in cursor.fetchall()]
    return all_threads

# ============================================================================

config = {"configurable": {"thread_id": "123"}}

# result = graph.invoke({"messages": [HumanMessage(content="Hi! I am Robert")]}, 
#     config=config)
# for m in result["messages"]:
#     m.pretty_print()

# print("====================================")

# result = graph.invoke({"messages": [HumanMessage(content="What's my name?")]}, 
#     config=config)
# for m in result["messages"]:
#     m.pretty_print()

# print("====================================")
# result = graph.invoke({"messages": [HumanMessage(content="I like the 49ers!")]}, 
#     config=config)
# for m in result["messages"]:
#     m.pretty_print()

print("====================================")
graph_state = graph.get_state(config)
print(graph_state)

# ============================================================================
# 关于 LangGraph Checkpoint 的说明：
# ============================================================================
#
# 1. Checkpoint 写入时机：
#    - LangGraph 会在每个"超步（superstep）"结束时自动将状态保存到数据库
#    - 超步（superstep）是指：所有当前可执行的节点（即所有前置节点已完成的节点）
#      并行执行的一个步骤
#    - 重要：如果有多个并行节点，系统会等待该超步中的所有并行节点都完成后，
#      才会统一保存一次 checkpoint，而不是每个节点执行完就写一次
#    - 这确保了状态持久化，支持错误恢复、人工干预等功能
#    - 示例：
#      * 如果节点A执行完，会立即保存一次 checkpoint
#      * 如果节点B和节点C并行执行，会等B和C都完成后，才保存一次 checkpoint
#
#    关于并行节点的执行机制：
#    - LangGraph 使用 BSP（Bulk Synchronous Parallel）模型
#    - 并行节点（如节点B和C）可能在不同的线程或进程中执行（这是LangGraph内部实现细节）
#    - 考虑到Python的GIL限制，LangGraph很可能使用多进程来实现真正的并行执行
#    - 但从用户角度看，它们是在同一个superstep中"逻辑上"并行执行的
#    - 无论实现细节如何，checkpoint都会在所有并行节点完成后统一保存
#
# 2. 如何删除已结束生命周期的 graph 的 checkpoint 记录：
#    使用 SqliteSaver 的 delete_thread() 方法可以删除特定 thread_id 的所有记录
#
#    示例：
#    # 当确定某个对话/线程已经结束时，删除其所有 checkpoint 记录
#    thread_id_to_delete = "123"
#    memory.delete_thread(thread_id_to_delete)
#
#    注意：delete_thread() 会删除该 thread_id 的所有检查点和写入操作，
#    所以在调用前请确保该线程的所有相关操作已完成且不再需要其数据
#
# 3. 批量清理示例：
#    # 如果需要清理多个线程
#    thread_ids_to_cleanup = ["123", "456", "789"]
#    for thread_id in thread_ids_to_cleanup:
#        memory.delete_thread(thread_id)
#
# 4. 查看所有线程（需要直接查询数据库）：
#    # 可以通过查询数据库来查看所有存储的 thread_id
#    cursor = conn.cursor()
#    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
#    all_threads = [row[0] for row in cursor.fetchall()]
#    print(f"所有线程ID: {all_threads}")
#
# ============================================================================