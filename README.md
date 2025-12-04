# LLM Agent Bug Study

All datasets used in this project are stored in the [Dataset](https://github.com/AnonymousRepo12/LLM-Agent-Bug-Study/tree/main/Dataset) folder.

## Installation

1. Download and install **Redis** on your local machine.
2. Install the project dependencies:
_pip install -r requirements.txt_

## Running the Agent

1. Start the Redis server:
_redis-server_
2. Create _.env_ file and paste your API key there. (Options: OPENAI_API_KEY for GPT o3 mini,OPENROUTER_API_KEY for Gemini 2.5 Flash or CLAUDE_API_KEY for Claude Sonnet 4)
3. Run the agent:
_python run_agent.py_


## Notes

- Make sure Redis is running before starting the agent.
- All required Python packages are listed in `requirements.txt`.

