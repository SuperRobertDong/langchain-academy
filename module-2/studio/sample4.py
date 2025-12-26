from langchain_core.messages import AIMessage, HumanMessage

messages = [AIMessage(content="Hello, how are you?", name="Model"),
            HumanMessage(content="I'm fine, thank you!", name="User")]
messages.append(AIMessage(content="Great! I'm sure you'll find some interesting information.", name="Model"))

for m in messages:
    m.pretty_print() 