from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import time

COOKIE_FILE = "../login/educative_cookies.pkl"
COURSE_SLUG = "database-design-fundamentals"
OUTPUT_FILE = "../sheet/data.txt"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

def login_with_cookies():
    driver.get("https://www.educative.io")
    time.sleep(2)

    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)

    for cookie in cookies:
        cookie.pop("sameSite", None)
        cookie.pop("expiry", None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error setting cookie: {e}")

    driver.get(f"https://www.educative.io/courses/{COURSE_SLUG}")
    print("Logged in and navigated to course.")

def expand_all_chapters_once():
    try:
        expand_all_div = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section[3]/div[1]/div/div/div[1]/div[2]/button/div'))
        )
        driver.execute_script("arguments[0].click();", expand_all_div)
        print("Clicked 'Expand All' button")
        time.sleep(2)
    except Exception as e:
        print("Failed to click 'Expand All' button:", e)

def get_all_lesson_links():
    expand_all_chapters_once()
    lesson_anchors = driver.find_elements(By.XPATH, '//section[3]//a[@href and starts-with(@href, "/courses/")]')

    lesson_links = []
    for a in lesson_anchors:
        try:
            title_span = a.find_element(By.CLASS_NAME, "Lesson_pageTitleText__2XIuy")
            lesson_title = title_span.text.strip()
        except:
            lesson_title = "Untitled Lesson"

        href = a.get_attribute("href")
        if href and (lesson_title, href) not in lesson_links:
            lesson_links.append((lesson_title, href))
    return lesson_links

def count_sql_widgets():
    try:
        run_buttons = driver.find_elements(By.XPATH, '//button[.//span[normalize-space()="Run"]]')
        return len(run_buttons)
    except:
        return 0

def process_lessons(lesson_links):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for idx, (lesson_title, link) in enumerate(lesson_links):
            driver.get(link)
            print(f"[{idx+1}/{len(lesson_links)}] Checking lesson: {lesson_title}")
            time.sleep(7)  # Wait for page to fully load
            run_count = count_sql_widgets()
            print(f"➡️  Found {run_count} SQL widget(s) in: {lesson_title}")
            if run_count > 0:
                f.write(f"{lesson_title}\n")

# --- MAIN EXECUTION ---
login_with_cookies()
time.sleep(5)
lesson_links = get_all_lesson_links()
print(f"\nFound {len(lesson_links)} lessons.")

process_lessons(lesson_links)

input("Press Enter to close the browser...")
driver.quit()
