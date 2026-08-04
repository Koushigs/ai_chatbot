# Import the pre-built agent creator
from langgraph.prebuilt import create_react_agent

# Import your model and tools from other files
from llm import model
from tools import all_tools

from prompts import SYSTEM_PROMPT as system_prompt

# Create the agent using the model, tools, and the new system prompt
react_agent = create_react_agent(model=model, tools=all_tools, prompt=system_prompt)
app = react_agent

print("Pre-built ReAct agent created successfully!")