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
from urllib.parse import urlparse
from DB.MiniStore import MiniStore
import unicodedata
from chunking import extract_info_about_target


@tool
def pydantic_doc_search(keyword: str) -> str:
    """
    Searches pydantic docs for the query and returns the text.
    """
    if keyword is not None:
        keyword = keyword.split(" ")[0].strip()
        keyword =  unicodedata.normalize("NFKC", keyword) 
            
    agent_keyword = "Pydantic"
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
        driver.get("https://docs.pydantic.dev/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # Click the search input
        search_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "md-search__inner"))
        )
        search_trigger.click()

        # Type the query
        search_input = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CLASS_NAME, "md-search__input"))
        )
        search_input.send_keys(keyword)
        time.sleep(2)
        

        # Wait for the results list to appear
        results_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ol.ais-Hits-list.md-search-result__list"))
        )

        # Find the first result and click it
        first_result = results_list.find_element(By.CSS_SELECTOR, "li.ais-Hits-item.md-search-result__item a")
        first_result.click()

        # Wait for the new page content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # Get the body text
        results_text = driver.find_element(By.TAG_NAME, "body").text
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # 1. grab the current URL and pull off the fragment (the part after '#')
        current_url = driver.current_url
        fragment = urlparse(current_url).fragment

        # 2. find the <h2> whose id matches that fragment
        header = driver.find_element(By.CSS_SELECTOR, f"h2#{fragment}")

        # 3. now walk its siblings, collecting text until you hit the next <h2>
        section_texts = []
        next_elem = header.find_element(By.XPATH, "following-sibling::*[1]")

        while True:
            if next_elem.tag_name.lower() == "h2":
                break
            section_texts.append(next_elem.text)
            try:
                # move to the next sibling
                next_elem = next_elem.find_element(By.XPATH, "following-sibling::*[1]")
            except:
                # no more siblings
                break

        # join everything
        results_text = "\n".join(section_texts)

        
        results_text = extract_info_about_target(results_text, keyword)
        db.save(agent_keyword, keyword, results_text)
        return results_text

    except Exception as e:
        traceback.print_exc()
        return f"No results found"
    finally:
        driver.quit()

