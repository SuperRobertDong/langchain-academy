from langgraph.graph import StateGraph,START,END

class MessageState(MessageState):
    pass

def tool_calling_llm(state: MessageState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}