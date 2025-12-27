"""
分析 interrupt() 和 Command(resume) 的行为

这个文件用于分析用户提供的代码示例，理解 interrupt() 恢复执行时的行为。
"""

import operator
import sys
from typing import Annotated, List, Literal, TypedDict
from langgraph import graph
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    nlist: Annotated[list[str], operator.add]

def node_a(state: State) -> Command[Literal["b", "c", END]]:
    print(f"node a is receiving {state['nlist']}", flush=True)  # 添加 flush=True 确保立即输出
    select = state['nlist'][-1]
    if select == "b":
        next_node = "b"
    elif select == "c":
        next_node = "c"
    elif select == "q":
        next_node = END
    else:
        # 关键点：interrupt() 会中断执行
        # 恢复执行时，函数会从头重新执行
        # 但是 interrupt() 会返回 Command(resume = ...) 中的值
        print("---调用 interrupt()，函数会中断---")
        admin = interrupt(f"Unexpected input {select}")
        print(f"---interrupt() 返回: {admin}---")
        if admin == "continue":
            next_node = "b"
        else:
            next_node = END
            select = "q"

    return Command(update = State(nlist = ["from the node a"]), goto = next_node)


def node_b(state: State) -> State:
    print(f"node b is receiving {state['nlist']}")
    note = "Hello World from Node b"
    return State(nlist = [note])

def node_c(state: State) -> State:
    print(f"node c is receiving {state['nlist']}")
    note = "Hello World from Node c"
    return State(nlist = [note])

builder = StateGraph(State) 
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_edge(START, "a")
builder.add_edge("b", END)
builder.add_edge("c", END)

memory = InMemorySaver()
config = {"configurable": {"thread_id": "1"}}
graph = builder.compile(checkpointer=memory)

print("=" * 60)
print("分析：interrupt() 恢复执行时的行为")
print("=" * 60)
print("\n关键问题：恢复执行时，node_a 是从头重新执行，还是从中断点继续？")
print("\n答案：会从头重新执行，但是 interrupt() 会返回恢复值")
print("\n执行流程：")
print("1. 第一次执行 node_a，遇到意外输入，调用 interrupt()，函数中断")
print("2. 恢复执行时，node_a 函数会从头重新执行")
print("3. 当执行到 interrupt() 这一行时，interrupt() 会返回 Command(resume = human) 中的值")
print("4. 然后继续执行后面的代码逻辑")
print("=" * 60)

while True:
    user = input("\nEnter b, c, or q to quit: ")
    print(f"\n---开始执行，输入值: {user}---", flush=True)
    initial_state = State(nlist = [user])
    print("---调用 graph.invoke()---", flush=True)
    result = graph.invoke(initial_state, config)
    print(f"Result: {result}", flush=True)
    if '__interrupt__' in result:
        print(f"Interrupt detected: {result}")
        msg = result['__interrupt__'][-1].value
        print(f"Interrupt message: {msg}")
        human = input(f"\n{msg}: ")
        human_response = Command(resume = human)
        print(f"\n---恢复执行，使用 Command(resume = '{human}')---")
        print("注意：node_a 会从头重新执行，但 interrupt() 会返回恢复值")
        result = graph.invoke(human_response, config)
        print(f"Result after resume: {result}")
    if user == "q":
        break

