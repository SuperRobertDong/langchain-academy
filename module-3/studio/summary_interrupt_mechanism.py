"""
总结：interrupt() 和恢复执行的完整机制

这个文件总结了 interrupt() 中断和恢复执行的完整机制。
"""

import operator
from typing import Annotated, Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    nlist: Annotated[list[str], operator.add]
    extra_info: str

def node_a(state: State) -> Command[Literal["b", "c", END]]:
    print(f"[node_a] 接收状态: {state['nlist']}, extra_info: {state.get('extra_info', 'N/A')}", flush=True)
    select = state['nlist'][-1]
    
    if select == "b":
        next_node = "b"
    elif select == "c":
        next_node = "c"
    elif select == "q":
        next_node = END
    else:
        print(f"[node_a] 遇到意外输入 '{select}'，调用 interrupt()", flush=True)
        # interrupt() 会中断执行
        admin = interrupt(f"Unexpected input {select}")
        # 恢复执行时，admin 会等于 Command(resume = ...) 中的值
        print(f"[node_a] interrupt() 返回: {admin}", flush=True)
        print(f"[node_a] 当前状态 extra_info: {state.get('extra_info', 'N/A')}", flush=True)
        
        if admin == "continue":
            next_node = "b"
        else:
            next_node = END

    return Command(update = State(nlist = ["from the node a"]), goto = next_node)


def node_b(state: State) -> State:
    print(f"[node_b] 接收状态: {state['nlist']}", flush=True)
    return State(nlist = ["Hello World from Node b"])

def node_c(state: State) -> State:
    print(f"[node_c] 接收状态: {state['nlist']}", flush=True)
    return State(nlist = ["Hello World from Node c"])

builder = StateGraph(State) 
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_edge(START, "a")
builder.add_edge("b", END)
builder.add_edge("c", END)

memory = InMemorySaver()
config = {"configurable": {"thread_id": "summary_example"}}
graph = builder.compile(checkpointer=memory)

print("=" * 70)
print("总结：interrupt() 和恢复执行的完整机制")
print("=" * 70)
print("\n关键机制：")
print("1. 遇到 interrupt() 时，graph 会中断当前执行")
print("2. 可以使用 graph.update_state(config, state) 更新状态")
print("3. 使用 graph.invoke(input, config) 继续执行，其中：")
print("   - 第一个参数可以是：")
print("     a) None (不更新状态)")
print("     b) 需要更新的 state (字典)")
print("     c) Command(resume=..., update=...)")
print("   - 第二个参数是 config (必须)")
print("4. 当传入 Command 时，继续执行到 interrupt() 时，")
print("   会自动返回 Command 中 resume 的值，而不会再次中断")
print("=" * 70)

# ========== 测试场景 1: 使用 update_state + Command(resume) ==========
print("\n" + "=" * 70)
print("场景 1: 先使用 update_state 更新状态，然后使用 Command(resume) 恢复")
print("=" * 70)

print("\n---步骤 1: 触发 interrupt---")
result = graph.invoke(State(nlist = ["x"], extra_info = ""), config)
print(f"结果: {result}")

if '__interrupt__' in result:
    print("\n---步骤 2: 使用 update_state 更新状态---")
    graph.update_state(
        config,
        {"extra_info": "通过 update_state 添加的信息"}
    )
    state = graph.get_state(config)
    print(f"更新后的状态: {state.values}")
    
    print("\n---步骤 3: 使用 Command(resume) 恢复执行---")
    # 第一个参数：Command(resume = ...)
    # 第二个参数：config
    result = graph.invoke(Command(resume = "continue"), config)
    print(f"最终结果: {result}")

# ========== 测试场景 2: 使用 Command(resume + update) 同时更新 ==========
print("\n" + "=" * 70)
print("场景 2: 使用 Command(resume + update) 同时恢复和更新状态")
print("=" * 70)

config2 = {"configurable": {"thread_id": "summary_example2"}}
print("\n---步骤 1: 触发 interrupt---")
result2 = graph.invoke(State(nlist = ["y"], extra_info = ""), config2)
print(f"结果: {result2}")

if '__interrupt__' in result2:
    print("\n---步骤 2: 使用 Command(resume + update) 同时恢复和更新---")
    # 第一个参数：Command(resume = ..., update = ...)
    # 第二个参数：config
    result2 = graph.invoke(
        Command(
            resume = "continue",
            update = State(extra_info = "通过 Command(update) 添加的信息")
        ),
        config2
    )
    print(f"最终结果: {result2}")

# ========== 测试场景 3: 使用 state 字典更新 ==========
print("\n" + "=" * 70)
print("场景 3: 使用 state 字典更新状态并继续执行")
print("=" * 70)

config3 = {"configurable": {"thread_id": "summary_example3"}}
print("\n---步骤 1: 触发 interrupt---")
result3 = graph.invoke(State(nlist = ["z"], extra_info = ""), config3)
print(f"结果: {result3}")

if '__interrupt__' in result3:
    print("\n---步骤 2: 使用 state 字典更新状态并继续执行---")
    # 第一个参数：state 字典
    # 第二个参数：config
    # 注意：这种方式不会让 interrupt() 返回值，而是更新状态后继续执行
    # 如果 node_a 中有检查状态的逻辑，可以使用这种方式
    result3 = graph.invoke(
        State(nlist = ["b"], extra_info = "通过 state 字典添加的信息"),
        config3
    )
    print(f"最终结果: {result3}")

print("\n" + "=" * 70)
print("总结：")
print("=" * 70)
print("1. graph.invoke(Command(resume=...), config) - interrupt() 会返回 resume 的值")
print("2. graph.invoke(State(...), config) - 更新状态，但 interrupt() 不会返回值")
print("3. graph.invoke(Command(resume=..., update=...), config) - 同时恢复和更新")
print("4. graph.update_state(config, state) + graph.invoke(Command(resume=...), config) - 分步操作")
print("=" * 70)

