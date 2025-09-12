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
import traceback
from chunking import extract_info_about_target

@tool
def autogen_doc_search(keyword: str) -> str:
    """
    Searches Autogen docs for the keyword and returns the text. 
    """
    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
       
    agent_keyword = "Autogen"
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
        driver.get(f"https://microsoft.github.io/autogen/stable//search.html?q={keyword}")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        all_results = driver.find_element(By.CLASS_NAME,"search")
        first_element = all_results.find_elements(By.CLASS_NAME, "kind-object")
        anchor_tag = first_element[0].find_element(By.TAG_NAME, "a")
        url = anchor_tag.get_attribute("href")
        
        driver.get(url)
        time.sleep(2)
        body = driver.find_element(By.CLASS_NAME, "bd-article")
        results_text = body.text
        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
    finally:
        driver.quit()

