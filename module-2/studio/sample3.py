from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph, START, MessagesState

class OverrallState(TypedDict):
    foo: int 
    added_key_1: str = "key_1"

class PrivateState(TypedDict):
    bar: int

def node_1(state: OverrallState) -> PrivateState:
    print("----node 1 is running----")
    return {"bar": state["foo"] + 1}

def node_2(state: PrivateState) -> OverrallState:
    print("----node 2 is running----")
    return {"foo": state["bar"] + 1}

builder = StateGraph(OverrallState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", END)
graph = builder.compile()

result = graph.invoke({"foo": 1, "added_key_1": "value_1"})
print(result)