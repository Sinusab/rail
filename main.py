from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
import requests
import json

# Telegram Bot settings
TELEGRAM_TOKEN = "7993551757:AAHmBKc23T8wlgCEYhmNwwLrG2qARH9N6gw"  # Replace with your bot token
TELEGRAM_CHAT_ID = "195375276" 

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

# Setup ChromeDriver with headless mode (no need to specify path)
service = Service()  # Selenium Manager will find Chromedriver
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=service, options=options)

# Load cookies and apply them
driver.get("https://www.raja.ir")  # Open site to set domain for cookies
with open("/app/raja_cookies.json", "r") as f:  # Path on Railway
    cookies = json.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
print("Cookies loaded")

# Refresh to apply cookies
driver.refresh()
print("Main page refreshed with cookies:", driver.current_url)

# Search URL for April 19, 1404 (14040119)
SEARCH_URL = "https://www.raja.ir/search?adult=1&child=0&infant=0&movetype=1&ischarter=false&fs=191&ts=1&godate=14040119&tickettype=Family&returndate=&numberpassenger=1&mode=Train&desctravel=%D9%82%D8%B7%D8%A7%D8%B1%20%D9%85%D8%B4%D9%87%D8%AF%20%D8%A8%D9%87%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86"

# Loop to check for tickets
while True:
    driver.get(SEARCH_URL)
    print("Search link refreshed:", driver.current_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "train-result"))
        )
        print("Results page loaded:", driver.current_url)
    except TimeoutException as e:
        print(f"Error loading results: {e}")
        driver.refresh()
        sleep(5)
        continue

    try:
        train_results = driver.find_elements(By.CLASS_NAME, "train-result")
        print(f"Number of trains found: {len(train_results)}")
        for result in train_results:
            train_name = result.find_element(By.CLASS_NAME, "train-name").text
            wagon_type = result.find_element(By.CLASS_NAME, "wagon-type").text
            print(f"Train name: {train_name}, Wagon type: {wagon_type}")

            if "اتوبوسی" not in train_name and "سالنی" not in train_name and \
               "اتوبوسی" not in wagon_type and "سالنی" not in wagon_type:
                capacity = result.find_element(By.CLASS_NAME, "field-value").text
                print(f"Capacity: {capacity}")

                if "تمام شد" not in capacity:
                    price_element = result.find_element(By.CLASS_NAME, "price")
                    price_text = price_element.text.replace(",", "")
                    price = int(price_text)
                    print(f"Price: {price} Rials")

                    if price <= 10000000:
                        try:
                            reserve_button = WebDriverWait(result, 5).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "lock-btn"))
                            )
                            reserve_button.click()
                            print(f"Train selected: {train_name}")

                            continue_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "btn-block"))
                            )
                            continue_button.click()
                            print("Continue purchase button clicked")

                            purchase_link = driver.current_url
                            message = f"Ticket found!\nTrain: {train_name}\nPrice: {price} Rials\nPurchase link: {purchase_link}"
                            send_telegram_message(message)
                            print("Notification sent. Stopping script...")
                            driver.quit()
                            exit()
                        except Exception as e:
                            print(f"Error reserving train {train_name}: {e}")
                    else:
                        print(f"Train {train_name} price ({price} Rials) exceeds 10,000,000 Rials")
                else:
                    print(f"Train {train_name} has no available capacity")
            else:
                print(f"Train {train_name} is bus-like or saloon, skipped")

        print("No suitable tickets found. Refreshing in 5 seconds...")
        sleep(5)
    except Exception as e:
        print(f"Error finding trains: {e}")
        driver.refresh()
        sleep(5)

driver.quit()
