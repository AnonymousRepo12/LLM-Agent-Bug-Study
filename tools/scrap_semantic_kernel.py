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
from langchain.tools import tool
import traceback

@tool
def semantic_kernel_doc_search(keyword): 
    """
    Searches semantic kernel docs for the query and returns the text.
    """
    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "SemanticKernel"
    db = MiniStore()
    if db.exists(agent_keyword, keyword):
        cached_result = db.get(agent_keyword, keyword)
        if cached_result:
            return cached_result

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://learn.microsoft.com/en-us/search/")
        time.sleep(2)  # Wait for the page to load
        selector = ".autocomplete-input.input.input-lg.control.has-icons-left.width-full"
        search_input = driver.find_element(By.CSS_SELECTOR, selector)
        search_input.send_keys(keyword)

        search_input.send_keys(Keys.ENTER)
        
        time.sleep(2)  # Wait for the search results to load
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-bi-name="result"]'))
        )

        # take the first result, find its <a> tag, grab the href, and navigate there
        first_result = results[0]
        link = first_result.find_element(By.TAG_NAME, "a")
        url = link.get_attribute("href")
        driver.get(url)
                
        time.sleep(1)  # Wait for the results to load

        results_text = driver.find_element(By.ID, "main").text

        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text
        

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
        
