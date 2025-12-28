import os
import json
from dotenv import load_dotenv

# 加载环境变量（从父目录的 .env 文件或当前目录的 .env 文件）
# 优先加载当前目录的 .env，如果没有则加载父目录的
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from langchain_community.chat_models import ChatTongyi

llm = ChatTongyi(
    model="qwen-plus",  # 或 "qwen-turbo", "qwen-max" 等
    model_kwargs={"temperature": 0},  # 通过 model_kwargs 设置温度
    streaming=True
)

# region analysis 

from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class Analyst(BaseModel):
    affiliation: str = Field(
        description="Primary affiliation of the analyst.",
    )
    name: str = Field(
        description="Name of the analyst."
    )
    role: str = Field(
        description="Role of the analyst in the context of the topic.",
    )
    description: str = Field(
        description="Description of the analyst focus, concerns, and motives.",
    )
    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"

class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(
        description="Comprehensive list of analysts with their roles and affiliations.",
    )

class GenerateAnalystsState(TypedDict):
    topic: str # Research topic
    max_analysts: int # Number of analysts
    human_analyst_feedback: str # Human feedback
    analysts: List[Analyst] # Analyst asking questions

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

analyst_instructions="""You are tasked with creating a set of AI analyst personas. Follow these instructions carefully:

1. First, review the research topic:
{topic}
        
2. Examine any editorial feedback that has been optionally provided to guide creation of the analysts: 
        
{human_analyst_feedback}
    
3. Determine the most interesting themes based upon documents and / or feedback above.
                    
4. Pick the top {max_analysts} themes.

5. Assign one analyst to each theme."""

def create_analysts(state: GenerateAnalystsState):
    
    """ Create analysts """
    
    topic=state['topic']
    max_analysts=state['max_analysts']
    human_analyst_feedback=state.get('human_analyst_feedback', '')
        
    # Enforce structured output
    structured_llm = llm.with_structured_output(Perspectives)

    # System message
    system_message = analyst_instructions.format(topic=topic,
                                                            human_analyst_feedback=human_analyst_feedback, 
                                                            max_analysts=max_analysts)

    # Generate question 
    analysts = structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Generate the set of analysts.")])
    
    # Write the list of analysis to state
    return {"analysts": analysts.analysts}

def human_feedback(state: GenerateAnalystsState):
    """ No-op node that should be interrupted on """
    pass

def should_continue(state: GenerateAnalystsState):
    """ Return the next node to execute """

    print(state.get('human_analyst_feedback', 'no human feedback'))
    # Check if human feedback
    human_analyst_feedback=state.get('human_analyst_feedback', None)
    if human_analyst_feedback:
        return "create_analysts"
    
    # Otherwise end
    return END

# builder = StateGraph(GenerateAnalystsState)
# builder.add_node("create_analysts", create_analysts)
# builder.add_node("human_feedback", human_feedback)
# builder.add_edge(START, "create_analysts")
# builder.add_edge("create_analysts", "human_feedback")
# builder.add_conditional_edges("human_feedback", should_continue, ["create_analysts", END])

# memory = MemorySaver()
# graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

# # Input
# max_analysts = 3 
# topic = "The benefits of adopting LangGraph as an agent framework"
# thread = {"configurable": {"thread_id": "1"}}

# # Run the graph until the first interruption
# for event in graph.stream({"topic":topic,"max_analysts":max_analysts,}, thread, stream_mode="values"):
#     # Review
#     analysts = event.get('analysts', '')
#     if analysts:
#         for analyst in analysts:
#             print(f"Name: {analyst.name}")
#             print(f"Affiliation: {analyst.affiliation}")
#             print(f"Role: {analyst.role}")
#             print(f"Description: {analyst.description}")
#             print("-" * 50)  

# # state = graph.get_state(thread)
# # print(state.next)

# # as_node 参数的作用：
# # 1. 告诉 LangGraph 这个状态更新是"模拟" human_feedback 节点执行后的结果
# # 2. 这样 checkpoint 系统会正确记录：这个状态更新来自 "human_feedback" 节点
# # 3. 这对调试、状态回放和继续执行很重要
# # 4. 如果不指定 as_node，LangGraph 不知道这个更新来自哪个节点，可能会导致状态不一致
# #
# # ⚠️ 关键理解：
# # - 执行 update_state(..., as_node="human_feedback") 后
# # - LangGraph 会认为 human_feedback 节点已经"完成"了
# # - 当继续执行时（调用 graph.stream(None, thread)）
# # - 会跳过 human_feedback 节点的实际执行，直接调用 should_continue 来决定下一步
# # - 这是因为 checkpoint 系统已经记录了 human_feedback 节点完成的状态
# #
# # 在这个例子中：
# # - human_feedback 是一个 no-op 节点（什么都不做）
# # - 但实际上它应该收集用户的反馈并更新状态
# # - 我们使用 update_state 手动模拟这个过程，告诉系统："这是 human_feedback 节点产生的更新"

# graph.update_state(
#     thread,
#     {
#         "human_analyst_feedback": "Add in someone from a startup to add an entrepreneur perspective"
#     }, 
#     as_node="human_feedback"  # 关键：指定这个更新来自哪个节点
# )

# # Continue the graph execution
# for event in graph.stream(None, thread, stream_mode="values"):
#     # Review
#     analysts = event.get('analysts', '')
#     if analysts:
#         for analyst in analysts:
#             print(f"Name: {analyst.name}")
#             print(f"Affiliation: {analyst.affiliation}")
#             print(f"Role: {analyst.role}")
#             print(f"Description: {analyst.description}")
#             print("-" * 50) 

# # state = graph.get_state(thread)
# # print(state.next)

# further_feedack = None
# graph.update_state(
#     thread,
#     {
#         "human_analyst_feedback": further_feedack
#     }, 
#     as_node="human_feedback"
# )

# # Continue the graph execution
# for event in graph.stream(None, thread, stream_mode="values"):
#     # Review
#     analysts = event.get('analysts', '')

# state = graph.get_state(thread)
# print(state.next)

# endregion analysis 

#region interview assistant

import operator
from typing import  Annotated
from langgraph.graph import MessagesState

class InterviewState(MessagesState):
    max_num_turns: int # Number turns of conversation
    context: Annotated[list, operator.add] # Source docs
    analyst: Analyst # Analyst asking questions
    interview: str # Interview transcript
    sections: list # Final key we duplicate in outer state for Send() API

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Search query for retrieval.")

question_instructions = """You are an analyst tasked with interviewing an expert to learn about a specific topic. 

Your goal is boil down to interesting and specific insights related to your topic.

1. Interesting: Insights that people will find surprising or non-obvious.
        
2. Specific: Insights that avoid generalities and include specific examples from the expert.

Here is your topic of focus and set of goals: {goals}
        
Begin by introducing yourself using a name that fits your persona, and then ask your question.

Continue to ask questions to drill down and refine your understanding of the topic.
        
When you are satisfied with your understanding, complete the interview with: "Thank you so much for your help!"

Remember to stay in character throughout your response, reflecting the persona and goals provided to you."""

def generate_question(state: InterviewState):
    """ Node to generate a question """

    # Get state
    analyst = state["analyst"]
    messages = state["messages"]

    # Generate question 
    system_message = question_instructions.format(goals=analyst.persona)
    question = llm.invoke([SystemMessage(content=system_message)]+messages)
        
    # Write messages to state
    return {"messages": [question]}

# endregion research assistant