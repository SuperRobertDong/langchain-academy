from typing import TypedDict, Annotated
from langgraph.graph import START, END, StateGraph, START, END
from operator import add

class TypedDictState(TypedDict):
    foo: Annotated[list[int], add]

def node_1(state: TypedDictState):
    print("----node 1 is running----")
    return {"foo": [state["foo"][-1] + 1]}

def node_2(state: TypedDictState):
    print("----node 2 is running----")
    return {"foo": [state["foo"][-1] + 1]}

def node_3(state: TypedDictState):
    print("----node 23 is running----")
    return {"foo": [state["foo"][-1] + 1]}

builder = StateGraph(TypedDictState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_1", "node_3")
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)
graph = builder.compile()

from langgraph.errors import InvalidUpdateError
try:
    result = graph.invoke({"foo": [1]})
    print(result)
except InvalidUpdateError as e:
    print(e)

