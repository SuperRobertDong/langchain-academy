import os
import json
import asyncio
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState

from typing_extensions import Literal

model = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0},  # 通过 model_kwargs 设置温度
    streaming=True  # 启用流式输出
)

# State 
class State(MessagesState):
    summary: str

# Define the logic to call the model
async def call_model(state: State):
    
    # Get summary if it exists
    summary = state.get("summary", "")
    
    # If there is summary, then we add it
    if summary:
        
        # Add summary to system message
        system_message = f"Summary of conversation earlier: {summary}"
        
        # Append summary to any newer messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    
    else:
        messages = state["messages"]
    
    # 使用 astream 来启用流式输出，这样 astream_events 才能捕获到 on_chat_model_stream 事件
    # 收集所有块并合并为完整消息（但在收集过程中，流式事件会实时触发）
    chunks = []
    async for chunk in model.astream(messages):
        chunks.append(chunk)
    
    # 合并所有块为完整消息
    if chunks:
        response = chunks[0]
        for chunk in chunks[1:]:
            response = response + chunk
    else:
        response = model.invoke(messages)

    return {"messages": response}

def summarize_conversation(state: State):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
        
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

# Determine whether to end or summarize the conversation
def should_continue(state: State)-> Literal ["summarize_conversation",END]:
    
    """Return the next node to execute."""
    
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return END

# Define a new graph
workflow = StateGraph(State)
workflow.add_node("conversation", call_model)
workflow.add_node(summarize_conversation)

# Set the entrypoint as conversation
workflow.add_edge(START, "conversation")
workflow.add_conditional_edges("conversation", should_continue)
workflow.add_edge("summarize_conversation", END)

# Compile
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# config = {"configurable": {"thread_id": "123"}}

# for chunk in graph.stream({"messages": [
#     HumanMessage(content="Hi! I am Robert")
# ]}, config=config, stream_mode="updates"):
#     print(chunk['conversation']['messages'].pretty_print())

# print("====================================")
# config = {"configurable": {"thread_id": "1234"}}

# for event in graph.stream({"messages": [
#     HumanMessage(content="Hi! I am Robert")
# ]}, config=config, stream_mode="values"):
#     for m in event['messages']:
#         m.pretty_print()

async def main():
    config = {"configurable": {"thread_id": "123"}}
    input_message = HumanMessage(content="Tell me about the 49ers NFL team")
    node_to_stream = "conversation"
    
    # 累积所有流式输出的内容
    full_content = ""
    
    # 监听 on_chat_model_stream 事件来获取流式输出
    async for event in graph.astream_events({"messages": [input_message]}, config, version="v2"):
        if event["event"] == "on_chat_model_stream" and event.get("metadata", {}).get("langgraph_node", "") == node_to_stream:
            # 从事件数据中提取 chunk 内容并实时打印
            data = event.get("data", {})
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, 'content'):
                chunk_content = chunk.content
                # 累积内容
                full_content += chunk_content
                # 流式输出
                node_name = event.get("metadata", {}).get("langgraph_node", "")
                print(f"node_name: {node_name},chunk_content: {chunk_content}")
    
    print()  # 换行
    print("\n" + "="*50)
    print("完整结果:")
    print("="*50)
    print(full_content)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
    print("====================================")