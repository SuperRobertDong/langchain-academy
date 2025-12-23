from langchain_core import messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

messages = [AIMessage(content=f"So you said you were reearching ocean mammals?", name="Model")]
messages.extend([HumanMessage(content="Yes, that's right.", name="User")])
messages.extend([AIMessage(content="Great! I'm sure you'll find some interesting information.", name="Model")])
messages.extend([HumanMessage(content="Thanks! I'll let you know if I find anything.", name="User")])

for m in messages:
    m.pretty_print()

