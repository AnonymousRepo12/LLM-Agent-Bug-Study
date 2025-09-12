from langchain.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import traceback
import time
import traceback
from DB.MiniStore import MiniStore
import unicodedata
from chunking import extract_info_about_target


@tool
def langgraph_doc_search(keyword: str) -> str:
    """
    Searches Langgraph docs for the query and returns the text.
    """

    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "LangGraph"
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
        driver.get("https://langchain-ai.github.io/langgraph/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        search_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "md-search__inner"))
        )
        search_trigger.click()
        

        # Focus and type into the actual input box
        search_input = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CLASS_NAME, "md-search__input"))
        )
        search_input.send_keys(keyword)
        time.sleep(2)
        search_input.send_keys(Keys.ENTER)
        time.sleep(1)

        

        results_text = driver.find_element(By.TAG_NAME, "body").text
        
        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text



    except Exception as e:
        traceback.print_exc()
        return f"No results found"
    finally:
        driver.quit()

