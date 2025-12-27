"""
测试：Command(resume) 和 update_state 能否同时使用

这个文件用于测试在恢复执行时，能否同时使用：
1. Command(resume = ...) 来让 interrupt() 返回值
2. update_state() 来更新状态
"""

import operator
from typing import Annotated, Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    nlist: Annotated[list[str], operator.add]
    extra_info: str  # 额外的状态字段

def node_a(state: State) -> Command[Literal["b", "c", END]]:
    print(f"[执行中] node a is receiving {state['nlist']}", flush=True)
    print(f"[执行中] extra_info = {state.get('extra_info', 'N/A')}", flush=True)
    select = state['nlist'][-1]
    
    if select == "b":
        next_node = "b"
    elif select == "c":
        next_node = "c"
    elif select == "q":
        next_node = END
    else:
        print(f"[执行中] 遇到意外输入 '{select}'，准备调用 interrupt()", flush=True)
        
        # interrupt() 会中断执行
        admin = interrupt(f"Unexpected input {select}")
        
        # 恢复执行时，admin 会等于 Command(resume = ...) 中的值
        print(f"[恢复执行] interrupt() 返回了: {admin}", flush=True)
        print(f"[恢复执行] extra_info = {state.get('extra_info', 'N/A')}", flush=True)
        
        if admin == "continue":
            next_node = "b"
        else:
            next_node = END

    return Command(update = State(nlist = ["from the node a"]), goto = next_node)


def node_b(state: State) -> State:
    print(f"[执行中] node b is receiving {state['nlist']}", flush=True)
    print(f"[执行中] extra_info = {state.get('extra_info', 'N/A')}", flush=True)
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
config = {"configurable": {"thread_id": "test_resume_and_update"}}
graph = builder.compile(checkpointer=memory)

print("=" * 70)
print("测试：Command(resume) 和 update_state 能否同时使用")
print("=" * 70)

# 测试：输入意外值触发 interrupt
print("\n=== 测试 1: 输入 'x' 触发 interrupt ===")
result = graph.invoke(State(nlist = ["x"], extra_info = ""), config)
print(f"\n结果: {result}")

if '__interrupt__' in result:
    print("\n检测到中断！")
    msg = result['__interrupt__'][-1].value
    print(f"中断消息: {msg}")
    
    print("\n" + "=" * 70)
    print("测试：先使用 update_state 更新状态，然后使用 Command(resume) 恢复")
    print("=" * 70)
    
    # 方法 1: 先使用 update_state 更新状态
    print("\n---步骤 1: 使用 update_state 更新 extra_info---")
    graph.update_state(
        config,
        {"extra_info": "这是通过 update_state 添加的信息"}
    )
    
    # 检查状态
    state = graph.get_state(config)
    print(f"更新后的状态: {state.values}")
    
    # 方法 2: 然后使用 Command(resume) 恢复执行
    print("\n---步骤 2: 使用 Command(resume = 'continue') 恢复执行---")
    human_response = Command(resume = "continue")
    result = graph.invoke(human_response, config)
    print(f"\n最终结果: {result}")
    
    print("\n" + "=" * 70)
    print("测试：同时使用 Command(resume) 和 Command(update) 更新状态")
    print("=" * 70)
    
    # 重新开始测试
    config2 = {"configurable": {"thread_id": "test_resume_and_update2"}}
    result2 = graph.invoke(State(nlist = ["y"], extra_info = ""), config2)
    
    if '__interrupt__' in result2:
        print("\n---使用 Command(resume) 和 Command(update) 同时更新---")
        # Command 可以同时包含 resume 和 update
        human_response2 = Command(
            resume = "continue",
            update = State(extra_info = "这是通过 Command(update) 添加的信息")
        )
        result2 = graph.invoke(human_response2, config2)
        print(f"\n最终结果: {result2}")

