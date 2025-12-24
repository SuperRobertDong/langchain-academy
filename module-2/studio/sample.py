from typing import TypedDict, Literal, Optional
import random
from dataclasses import dataclass

@dataclass
class TypedDictState:
    name: str
    mood: Optional[Literal["happy", "sad", ""]] = None

# class TypedDictState(TypedDict):
#     name: str
#     mood: Optional[Literal["happy", "sad", ""]]

from langgraph.graph import START, END, StateGraph, START, END

def node_1(state: TypedDictState):
    print("----node 1 is running----")
    return {"name": state.name + " is ..."}

def node_2(state: TypedDictState):
    print("----node 2 is running----")
    return {"mood": "happy"}

def node_3(state: TypedDictState):
    print("----node 3 is running----")
    return {"mood": "sad"}

def decide_node(state: TypedDictState) -> Literal["node_2", "node_3"]:
    if random.random() < 0.5:
        return "node_2"
    else:
        return "node_3"

builder = StateGraph(TypedDictState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_node("decide_node", decide_node)
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_node)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)
graph = builder.compile()

result = graph.invoke(TypedDictState(name="John"))
print(result)