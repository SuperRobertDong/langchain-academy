from typing import TypedDict, Annotated
from langgraph.graph import START, END, StateGraph, START, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, RemoveMessage
from langgraph.graph.message import add_messages

class CustomerMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    added_key_1: str
    added_key_2: str

class ExtenededMesageState(MessagesState):
    added_key_1: str
    added_key_2: str

initial_messages = [HumanMessage(content="Hello, how are you?", name="John", id="1"),
                    AIMessage(content="I'm fine, thank you!", name="Model", id="2"),
                    HumanMessage(content="What is your name?", name="John", id="3")]
new_message = AIMessage(content="What is your name?", name="Model", id="4")
merged_messages = add_messages(initial_messages, new_message)

delete_messages = [RemoveMessage(id=m.id) for m in merged_messages[:-2]]
print(delete_messages)
print(merged_messages)
merged_messages = add_messages(merged_messages, delete_messages)
print(merged_messages)


