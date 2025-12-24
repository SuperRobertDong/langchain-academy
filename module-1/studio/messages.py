from typing import Annotated, Type, TypedDict 
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages

class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

initial_messages = [AIMessage(content="Hello! How can I assist you?", name="Model"), 
    HumanMessage(content="I'm looking for information on marine biology", name="Robert")]

new_message = AIMessage(content="SUre, I can help with that. What specially are you interested in?", name="Model")

add_messages(initial_messages, new_message)

print(initial_messages)