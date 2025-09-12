import os
import openai
import tiktoken
from dotenv import load_dotenv
load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

def count_tokens(text, model="o3-mini-2025-01-31"):
    text.replace("endoftext", " ") 
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text, allowed_special={"<|endoftext|>"}))

def chunk_text(text, max_tokens_per_chunk=3000, model="o3-mini-2025-01-31"):
    chunks = []
    current_chunk = []
    current_tokens = 0
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph_tokens = count_tokens(paragraph, model=model)
        if current_tokens + paragraph_tokens > max_tokens_per_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_tokens = paragraph_tokens
        else:
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    return chunks

def make_target_prompt(text_chunk, target):
    return f"""You are given part of a codebase or documentation or discussion. If it's a codebase or documentation, follow the instructions below:
Search only for information specifically related to "{target}".

If the text below includes any content specifically about "{target}", extract only that (such as its definition, signature, description, or comments directly referencing it). 

Do not make anything up. Do not returns the copyright texts. If there's nothing clearly related to "{target}" in the input, reply with: "No relevant information found."

If it's a discussion, follow the instruction below:

Summarize the problem that the user is facing and the solution if provided. If the discussion does not provide any solution, reply with: "No relevant information found."
Input:
{text_chunk}

Output:
"""

def call_llm(prompt, model="o3-mini-2025-01-31"):
    
    if(model.startswith("claude")):
        try:
            client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
            response = client.messages.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0
            )
            return response.content[0].text
        except Exception as e:
            return f"[Error calling Claude: {e}]"
    if(model.startswith("google")):
        try:
            client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                
                
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Error calling Gemini: {e}]"
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error calling LLM: {e}]"

def extract_info_about_target(full_text, target,  max_total_tokens=5000):
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    model = "o3-mini-2025-01-31" if not claude_api_key else "claude-sonnet-4-20250514"
    model = "google/gemini-2.5-flash" if os.getenv("OPENROUTER_API_KEY") else model
    total_tokens = count_tokens(full_text, model)
    if total_tokens < max_total_tokens - 1000:
        prompt = make_target_prompt(full_text, target)
        response = call_llm(prompt, model)
        return response 
    
    chunks = chunk_text(full_text, max_tokens_per_chunk=3000, model=model)
    relevant_outputs = []
    for chunk in chunks:
        prompt = make_target_prompt(chunk, target)
        response = call_llm(prompt, model)
        if response and "No relevant information found" not in response:
            relevant_outputs.append(response)
    
    return "\n\n".join(relevant_outputs).strip() if relevant_outputs else ""

