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
def openai_search(keyword: str) -> str:
    """
    Searches openai OpenAI Developer Community for the query and returns the text.
    """
    if keyword is not None:
        keyword = keyword.strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "OpenAI"
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
        driver.get(f"https://community.openai.com/search?q={keyword}")
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        # search_input = driver.find_element(By.ID, "ember23")
        # search_input.clear()
        # search_input.send_keys(keyword + Keys.RETURN)
        # time.sleep(2)

        question_container = driver.find_element(By.CLASS_NAME, "fps-result-entries")

        list_items = question_container.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        
        if list_items:
            anchor = list_items[0].find_element(By.CLASS_NAME, "search-link")
            # Get the href attribute
            link_url = anchor.get_attribute("href")
            
            # Navigate to the URL
            driver.get(link_url)
            time.sleep(2)

            result = driver.find_element(By.CLASS_NAME, "container.posts")
            results_text = result.text
            results_text = extract_info_about_target(results_text, keyword)
            db.save(agent_keyword, keyword, results_text)
            return results_text
        
        else:
            return "No results found for the query."

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
    finally:
        driver.quit()
