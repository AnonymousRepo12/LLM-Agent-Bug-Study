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
from langchain.tools import tool


@tool
def crewai_doc_search(keyword: str) -> str:
    """
    Searches Crewai docs for the keyword and returns the text. 
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    
    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "CrewAI"
    db = MiniStore()
    if db.exists(agent_keyword, keyword):
        cached_result = db.get(agent_keyword, keyword)
        if cached_result:
            return cached_result
            
    try:
        driver.get("https://docs.crewai.com/en/introduction/")
            

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)

        body = driver.find_element(By.TAG_NAME, "body")
        if platform.system() == "Darwin":
            body.send_keys(Keys.COMMAND + "k")
        else:
            body.send_keys(Keys.CONTROL + "k")
        time.sleep(2)
        
        # Type search query
        input_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[4]/div/div/div/div[2]/div/div[1]/input"))
        )
        print("input element found")

        input_element.click()        
        input_element.clear()  # Optional: clear any existing text
        input_element.send_keys(keyword)
        time.sleep(1)
        input_element.send_keys(Keys.ENTER)
        
        time.sleep(1)

        body_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1)

        results_text = body_element.text
        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text
    

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
