import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from typing import TypedDict
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig

class UserProfile(TypedDict):
    user_name: str
    interests: list[str]

model = ChatTongyi(
    model="qwen-plus",
    model_kwargs={"temperature": 0},
    streaming=False
)

model_with_structure = model.with_structured_output(UserProfile)

class MessagePrinter(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        actual_messages = messages[0] if messages and isinstance(messages[0], list) else messages
        
        prompt_parts = []
        for msg in actual_messages:
            if hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, str):
                    prompt_parts.append(content)
        
        print("\n".join(prompt_parts))

messages = [HumanMessage(content="My name is Lance, I like to bike.")]
printer = MessagePrinter()

config = RunnableConfig(callbacks=[printer])

model_with_structure.invoke(messages, config=config)