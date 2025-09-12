from langchain.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import time
from DB.MiniStore import MiniStore
import unicodedata
from chunking import extract_info_about_target
import traceback


@tool
def github_discussion_search(arg: str) -> str: #wrapper function for the tool, since the tool requires two arguments, but the agent only passes one argument.
    """
    Searches github discussion for the query and returns the text.
    """
    parts = [s.strip() for s in arg.split("_")]
    if len(parts) != 2 or not all(parts):
        return "Invalid input to github_discussion_search. Please provide exactly one underscore-separated string in the format keyword_libraryName."
        
    keyword, library_name = parts
    return github_search(keyword, library_name)


def github_search(keyword: str, library_name:str) -> str:
    
    library_name = library_name.strip().lower()
    library_name = unicodedata.normalize("NFKC", library_name)
    
    url_map = {"langchain":"https://github.com/langchain-ai/langchain/discussions",
               "langgraph":"https://github.com/langchain-ai/langgraph/discussions",
               "autogen":"https://github.com/microsoft/autogen/discussions",
               "crewai":"https://github.com/crewAIInc/crewAI/discussions" ,
               "langchainjs":"https://github.com/langchain-ai/langchainjs/discussions",
               "llamaindex":"https://github.com/run-llama/llama_index/discussions",
               "pydantic":"https://github.com/pydantic/pydantic/discussions",
               "semantickernel":"https://github.com/microsoft/semantic-kernel/discussions"
               }
    if library_name not in url_map.keys():
        return f"Library '{library_name}' not supported. Supported libraries: {', '.join(url_map.keys())}"
    
    if keyword is not None:
        keyword = keyword.strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "GitHub_"+library_name
    db = MiniStore()
    if db.exists(agent_keyword, keyword):
        cached_result = db.get(agent_keyword, keyword)
        if cached_result:
            return cached_result
        
    options = Options()
    options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    try:
        
        base_url = url_map[library_name]    
        driver.get(base_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        search_input = driver.find_element(By.ID, "discussions-search-combobox")
        search_input.clear()

        search_input.send_keys(keyword + Keys.RETURN)

        time.sleep(2)
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "lh-condensed"))
        )

        # Filter for elements that have all expected classes
        matching_elements = [el for el in results if "pl-2" in el.get_attribute("class") and "pr-3" in el.get_attribute("class") and "flex-1" in el.get_attribute("class")]
       
        # Click the first one
        if matching_elements:
            first = matching_elements[0]
            
            link = first.find_element(By.TAG_NAME, "a")
            url  = link.get_attribute("href")
            driver.get(url)
            time.sleep(2)
            discussion_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                ".discussion.js-discussion.js-socket-channel.js-updatable-content"
            ))
            )
            results_text = discussion_element.text
            results_text = extract_info_about_target(results_text, keyword)
            db.save(agent_keyword, keyword, results_text)
            return results_text
            
        else:
            return "No matching elements found."
         

    except Exception as e:
        return f"Error during LangChain doc search: {str(e)}"
    finally:
        driver.quit()

