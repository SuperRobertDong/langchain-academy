"""
示例：在函数中间中断并根据人工返回结果决定执行逻辑

这个示例展示了：
1. step1: 打印信息，然后使用 interrupt 中断等待人工决策
2. 根据人工决策结果，路由到 step2 或 step3
3. step2 和 step3: 简单的打印，显示它们执行了
"""

from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import interrupt

class State(TypedDict):
    decision: str  # 人工决策：'step2' 或 'step3'


def step1(state: State) -> State:
    """
    Step 1: 打印信息，然后中断等待人工决策
    
    关键逻辑：
    - 先执行打印操作（证明是从头执行的）
    - 检查是否已经有人工决策
    - 如果没有决策，调用 interrupt 中断执行
    - 如果已有决策，返回状态继续执行
    """
    print("---Step 1: 开始执行---")
    print("这是从函数开头执行的，我知道这个是从头执行的")
    
    # 检查是否已经有人工决策
    if not state.get('decision'):
        # 如果没有决策，中断等待
        print("---中断：等待人工决策---")
        interrupt(
            "需要人工决策。请选择执行 step2 还是 step3？\n"
            "请在状态中设置 decision 为 'step2' 或 'step3'"
        )
    
    # 如果已有决策，继续执行
    print(f"---检测到决策: {state['decision']}，继续处理---")
    return state


def step2(state: State) -> State:
    """Step 2: 简单的打印，显示执行了"""
    print("---Step 2: 执行了---")
    return state


def step3(state: State) -> State:
    """Step 3: 简单的打印，显示执行了"""
    print("---Step 3: 执行了---")
    return state


# 构建图
builder = StateGraph(State)
builder.add_node("step1", step1)
# 路由逻辑直接读取 step1 中设置的 decision 值
builder.add_conditional_edges(
    "step1",
    lambda state: state.get('decision', END),  # 直接读取 step1 中设置的 decision
    {
        "step2": "step2",
        "step3": "step3",
        END: END
    }
)
builder.add_node("step2", step2)
builder.add_node("step3", step3)
builder.add_edge("step2", END)
builder.add_edge("step3", END)
builder.add_edge(START, "step1")

# 编译图
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


# ========== 执行示例 ==========

if __name__ == "__main__":
    print("=" * 60)
    print("场景 1: 选择执行 step2")
    print("=" * 60)
    
    thread_config = {"configurable": {"thread_id": "example1"}}
    
    # 第一次执行：step1 打印并中断
    print("\n---第一次执行：step1 打印并中断---")
    for event in graph.stream(
        {"decision": ""},  # 初始状态：没有决策
        thread_config,
        stream_mode="values"
    ):
        print(event)
    
    # 检查状态
    state = graph.get_state(thread_config)
    print(f"\n当前状态: {state.values}")
    print(f"下一个节点: {state.next}")
    
    # 人工决策：选择 step2
    print("\n---人工决策：选择 step2---")
    graph.update_state(
        thread_config,
        {"decision": "step2"}
    )
    
    # 继续执行：根据决策路由到 step2
    print("\n---继续执行：根据决策执行---")
    for event in graph.stream(None, thread_config, stream_mode="values"):
        print(event)
    
    print("\n" + "=" * 60)
    print("场景 2: 选择执行 step3")
    print("=" * 60)
    
    # 重新开始，使用新的 thread_id
    thread_config2 = {"configurable": {"thread_id": "example2"}}
    
    print("\n---第一次执行：step1 打印并中断---")
    for event in graph.stream(
        {"decision": ""},  # 初始状态：没有决策
        thread_config2,
        stream_mode="values"
    ):
        print(event)
    
    # 人工决策：选择 step3
    print("\n---人工决策：选择 step3---")
    graph.update_state(
        thread_config2,
        {"decision": "step3"}
    )
    
    # 继续执行：根据决策路由到 step3
    print("\n---继续执行：根据决策执行---")
    for event in graph.stream(None, thread_config2, stream_mode="values"):
        print(event)
