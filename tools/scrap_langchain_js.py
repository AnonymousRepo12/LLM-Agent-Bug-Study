from langchain.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import time
import traceback
from DB.MiniStore import MiniStore
import unicodedata
from chunking import extract_info_about_target


@tool
def langchain_js_doc_search(keyword: str) -> str:
    """
    Searches LangChain-js docs for the query and returns the text.
    """

    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "LangChainJS"
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
        driver.get("https://js.langchain.com/docs/introduction/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        body = driver.find_element(By.TAG_NAME, "body")
        if platform.system() == "Darwin":
            body.send_keys(Keys.COMMAND + "k")
        else:
            body.send_keys(Keys.CONTROL + "k")

        search_box = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Search docs']"))
        )
        search_box.send_keys(keyword)
        time.sleep(1)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(2)

        results = driver.find_element(By.TAG_NAME, "body")
        results_text = results.text
        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
    finally:
        driver.quit()

