"""
解释 interrupt() 和 Command(resume) 的机制

这个文件用于详细解释 LangGraph 引擎如何处理 interrupt() 的返回值。
"""

import operator
from typing import Annotated, Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    nlist: Annotated[list[str], operator.add]

def node_a(state: State) -> Command[Literal["b", "c", END]]:
    print(f"[执行中] node a is receiving {state['nlist']}", flush=True)
    select = state['nlist'][-1]
    print(f"[执行中] select = {select}", flush=True)
    
    if select == "b":
        next_node = "b"
        print(f"[执行中] 选择 b，直接路由到 node_b", flush=True)
    elif select == "c":
        next_node = "c"
        print(f"[执行中] 选择 c，直接路由到 node_c", flush=True)
    elif select == "q":
        next_node = END
        print(f"[执行中] 选择 q，结束", flush=True)
    else:
        # 关键点：当执行到这里时，会调用 interrupt()
        print(f"[执行中] 遇到意外输入 '{select}'，准备调用 interrupt()", flush=True)
        print(f"[执行中] 调用 interrupt() 之前...", flush=True)
        
        # interrupt() 会中断执行
        # 恢复执行时，函数会从头重新执行
        # 但是当再次执行到这一行时，interrupt() 会返回 Command(resume = ...) 中的值
        admin = interrupt(f"Unexpected input {select}")
        
        # 恢复执行时，会从这里继续
        # admin 的值就是 Command(resume = "continue") 中的 "continue"
        print(f"[恢复执行] interrupt() 返回了: {admin}", flush=True)
        print(f"[恢复执行] admin 的类型: {type(admin)}", flush=True)
        
        if admin == "continue":
            next_node = "b"
            print(f"[恢复执行] admin == 'continue'，路由到 node_b", flush=True)
        else:
            next_node = END
            print(f"[恢复执行] admin != 'continue'，结束", flush=True)

    return Command(update = State(nlist = ["from the node a"]), goto = next_node)


def node_b(state: State) -> State:
    print(f"[执行中] node b is receiving {state['nlist']}", flush=True)
    return State(nlist = ["Hello World from Node b"])

def node_c(state: State) -> State:
    print(f"[执行中] node c is receiving {state['nlist']}", flush=True)
    return State(nlist = ["Hello World from Node c"])

builder = StateGraph(State) 
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_edge(START, "a")
builder.add_edge("b", END)
builder.add_edge("c", END)

memory = InMemorySaver()
config = {"configurable": {"thread_id": "explain_resume"}}
graph = builder.compile(checkpointer=memory)

print("=" * 70)
print("解释：interrupt() 如何从 Command(resume) 获取返回值")
print("=" * 70)
print("\n关键机制：")
print("1. 当调用 interrupt() 时，函数执行会中断")
print("2. 恢复执行时，使用 Command(resume = value) 来传递恢复值")
print("3. LangGraph 引擎会重新执行被中断的节点函数")
print("4. 当执行到 interrupt() 这一行时，interrupt() 会返回 Command(resume = ...) 中的值")
print("5. 这样函数就可以继续执行，而不需要检查状态")
print("=" * 70)

# 测试：输入意外值触发 interrupt
print("\n=== 测试：输入 'x' 触发 interrupt ===")
result = graph.invoke(State(nlist = ["x"]), config)
print(f"\n结果: {result}")

if '__interrupt__' in result:
    print("\n检测到中断！")
    msg = result['__interrupt__'][-1].value
    print(f"中断消息: {msg}")
    
    print("\n" + "=" * 70)
    print("恢复执行：使用 Command(resume = 'continue')")
    print("=" * 70)
    print("\n关键点：")
    print("- LangGraph 引擎会重新执行 node_a 函数")
    print("- 当执行到 interrupt() 这一行时，interrupt() 会返回 'continue'")
    print("- 这样 admin 变量就直接等于 'continue'，不需要检查状态")
    print("=" * 70)
    
    human_response = Command(resume = "continue")
    print(f"\n使用 Command(resume = 'continue') 恢复执行...")
    result = graph.invoke(human_response, config)
    print(f"\n最终结果: {result}")

