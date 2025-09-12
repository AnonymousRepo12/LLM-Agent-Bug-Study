import os
from dotenv import load_dotenv
from label import classify_post_and_answer
import traceback
import json
import re
from langchain.callbacks import get_openai_callback
import time
load_dotenv() 

from langchain.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import initialize_agent, Tool, AgentType
from tools.scrap_langchain import langchain_doc_search
from tools.scrap_autogen import autogen_doc_search
from tools.scrap_crewai import crewai_doc_search
from tools.scrap_langchain_js import langchain_js_doc_search
from tools.scrap_langgraph import langgraph_doc_search
from tools.scrap_llamaindex import llamaindex_doc_search
from tools.scrap_pydantic import pydantic_doc_search
from tools.scrap_semantic_kernel import semantic_kernel_doc_search
from tools.scrap_openai import openai_search
from tools.scrap_github import github_discussion_search
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# Check for Claude API key
claude_api_key = os.getenv("CLAUDE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not claude_api_key and not openai_api_key and not openrouter_api_key:
    raise ValueError("Please set either CLAUDE_API_KEY, OPENAI_API_KEY or OPENROUTER_API_KEY in your environment variables.")

if claude_api_key:
    print("Using Claude model")
    model_name = "claude-sonnet-4-20250514"
    llm = ChatAnthropic(
        anthropic_api_key=claude_api_key,
        model_name=model_name,
        temperature=1,
    )
elif openrouter_api_key:
    print("Using Gemini model")
    model_name = "google/gemini-2.5-flash"
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        openai_api_key=openrouter_api_key,
        model_name=model_name,
        temperature=1,
    )
else:
    print("Using OpenAI model")
    model_name = "o3-mini-2025-01-31" # "gpt-5-2025-08-07" #
    llm = ChatOpenAI(
        openai_api_key=openai_api_key,
        model_name=model_name,
        temperature=1,
    )
    agent_type = AgentType.OPENAI_FUNCTIONS 


tools = [
   Tool(
    name="SearchLangchainDocs",
    func=lambda query: langchain_doc_search.run(query),
    description=(
        "Use this to look up method names or class references in Langchain documentation. "
        "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
    )
),
   Tool(
    name="SearchAutogenDocs",
    func=lambda query: autogen_doc_search.run(query),
    description=(
        "Use this to look up method names or class references in AutoGen documentation. "
        "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
    )
),
Tool(
    name="SearchCrewAIgenDocs",
    func=lambda query: crewai_doc_search.run(query),
    description=(
        "Use this to look up method names or class references in CrewAI documentation. "
        "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
    )
), 
Tool(
    name="SearchLangchainJSgenDocs",
    func=lambda query: langchain_js_doc_search.run(query),
    description=(
        "Use this to look up method names or class references in LangchinJS documentation. "
        "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
    )
    ),
  Tool(
    name="SearchLangGraphDocs",
    func=lambda query: langgraph_doc_search.run(query),
    description=(
        "Use this to look up method names or class references in LangGraph documentation. "
        "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
    )
    ),
    Tool(
        name="SearchLlamaIndexDocs",
        func=lambda query: llamaindex_doc_search.run(query),
        description=(
            "Use this to look up method names or class references in LlamaIndex documentation. "
            "Use only when specific keywords (e.g., 'OpenAPIAgent', 'endpoints') are present. "
        )
    ),

    Tool(
        name="SearchPydanticDocs",
        func=lambda query: pydantic_doc_search.run(query),
        description=(
            "Use this to look up method names or class references in Pydantic documentation. "
            "Use only when specific keywords (e.g., 'model_dump_json') are present. "
        )
    ), 

    Tool(
        name="SearchSemanticKernelDocs",
        func=lambda query: semantic_kernel_doc_search.run(query),
        description=(
            "Use this to look up method names or class references in Semantic Kernel documentation. "
            "Use only when specific keywords (e.g., 'SetSwitch') are present. "
        )
    ), 
    Tool(
        name="SearchOpenAIDiscussion",
        func=lambda query: openai_search.run(query),
        description=(
            "Use this to look up method names or class references in OpenAI community discussin."
        )
    ),
    Tool(
        name="SearchGitHubDiscussion",
        func=lambda query: github_discussion_search.run(query),
        description=(
            "Use this to look up method names or class references in GitHub discussion. "
            "You should pass one argument as the input and the input format should be yourSearchText_libraryName."
            "Supported libraries: langchain, langgraph, autogen, crewai, langchainjs, llamaindex, pydantic, semantic_kernel."
        )
    ),
]



agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description", #AgentType.OPENAI_FUNCTIONS, #
    verbose=True,
    # agent_kwargs={"stop": []},
)



def run_agent_with_post(post_text: str):
    return agent.run(post_text)



if __name__ == "__main__":
    df = pd.read_csv("file_name.csv")
    data = []
    for _, row in df.iloc[:].iterrows():
        title = row['title']
        
        body =  row['body']
        
        
        example_post = f"""
        You are an expert in finding bugs. You are given Stack Overflow post. Your task is to indentify where the problem is. You have access to tools that will search the documentation or discussion pages for you. You should use them linstead of assuming an you are correct. 
        Title: {title} \n\n
        Body: {body} \n\n
        """
        try:
            result = run_agent_with_post(example_post)
            
            prediction = classify_post_and_answer(example_post, result,llm,"claude" if claude_api_key else "openai") #
            if(openrouter_api_key):
                cleaned = re.sub(r"^```json|```$", "", prediction["raw_response"].strip(), flags=re.MULTILINE).strip()
                prediction = json.loads(cleaned)
            data.append({
                "id": id,
                "reasoning": result,
                "bug_type": prediction['bug_type'],
                "Language": prediction['Language'],
                "Component": prediction['Component'],
                "Framework": prediction['Framework'],
                "root_cause": prediction['root_cause'],
                "effect": prediction['effect'],
                "bug_type_rational": prediction['bug_type_rational'],
                "root_cause_rational": prediction['root_cause_rational'],
                "effect_rational": prediction['effect_rational'],
                
            })
            
        except Exception as e:
            print(f"Error processing post ID {id}: {e}")
            traceback.print_exc()
            end_time = time.perf_counter()
            
            data.append({
                "id": id,
                "reasoning": "Error occurred",
                "bug_type": "N/A",
                "Language": "N/A",
                "Component": "N/A",
                "Framework": "N/A",
                "root_cause": "N/A",
                "effect": "N/A",
                "bug_type_rational": "N/A",
                "root_cause_rational": "N/A",
                "effect_rational": "N/A",
                
            })
        

   