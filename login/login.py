from selenium import webdriver
import pickle
import time

COOKIE_FILE = "educative_cookies.pkl"

driver = webdriver.Chrome()
driver.get("https://www.educative.io")

print("Please log in to Educative manually...")
time.sleep(60)


cookies = driver.get_cookies()
with open(COOKIE_FILE, "wb") as f:
    pickle.dump(cookies, f)

print(f"Cookies saved to {COOKIE_FILE}")
driver.quit()