import pytest

pytest.importorskip("selenium")

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def test_login_page_links_to_register(browser, live_server):
    browser.get(f"{live_server}/login")

    assert "Log In" in browser.page_source
    assert browser.find_element(By.LINK_TEXT, "Sign up").get_attribute("href").endswith("/register")


def test_user_can_register_and_login(browser, live_server):
    register_user(browser, live_server, "seleniumuser", "selenium@example.com")
    login_user(browser, live_server, "seleniumuser")

    assert "Study Buddy" in browser.page_source
    assert "/studybuddy" in browser.current_url


def test_user_can_create_study_session(browser, live_server):
    login_user(browser, live_server)
    browser.find_element(By.ID, "openCreateModal").click()

    browser.find_element(By.ID, "unit_code").send_keys("CITS5505")
    browser.find_element(By.ID, "topic").send_keys("Selenium Created Session")
    browser.find_element(By.ID, "description").send_keys("Created from a Selenium test.")
    browser.find_element(By.ID, "host_name").send_keys("Study Student")
    browser.find_element(By.ID, "capacity").send_keys("4")
    Select(browser.find_element(By.ID, "day")).select_by_value("Mon")
    browser.find_element(By.ID, "time").send_keys("10:00 AM")
    Select(browser.find_element(By.ID, "mode")).select_by_value("online")
    browser.find_element(By.CSS_SELECTOR, ".session-form button[type='submit']").click()

    wait = WebDriverWait(browser, 5)
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium Created Session"))
    assert "Selenium Created Session" in browser.page_source


def test_my_sessions_shows_joined_sessions(browser, live_server):
    login_user(browser, live_server)
    browser.get(f"{live_server}/my-sessions?view=joined")

    wait = WebDriverWait(browser, 5)
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "My Sessions"))
    assert "My Sessions" in browser.page_source
    assert "Showing: Joined" in browser.page_source


def test_session_detail_allows_joined_user_to_post_message(browser, live_server):
    login_user(browser, live_server)
    browser.get(f"{live_server}/studybuddy")
    browser.find_element(By.XPATH, "//button[normalize-space()='Join Session']").click()

    wait = WebDriverWait(browser, 5)
    wait.until(EC.presence_of_element_located((By.NAME, "content")))
    browser.find_element(By.NAME, "content").send_keys("Selenium discussion question")
    browser.find_element(By.CSS_SELECTOR, ".message-form button[type='submit']").click()

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium discussion question"))
    assert "Selenium discussion question" in browser.page_source


def test_logout_returns_user_to_login_page(browser, live_server):
    login_user(browser, live_server)
    wait = WebDriverWait(browser, 5)
    browser.find_element(By.ID, "profileToggle").click()
    wait.until(EC.visibility_of_element_located((By.ID, "profileMenu")))
    browser.find_element(By.CSS_SELECTOR, ".profile-menu-form button").click()

    wait.until(EC.url_contains("/login"))
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Log In"))
    assert "Log In" in browser.page_source
    assert "/login" in browser.current_url


def register_user(browser, live_server, username, email):
    wait = WebDriverWait(browser, 5)
    browser.get(f"{live_server}/register")
    browser.find_element(By.ID, "register-username").send_keys(username)
    browser.find_element(By.ID, "register-email").send_keys(email)
    browser.find_element(By.ID, "register-password").send_keys("Password1")
    browser.find_element(By.ID, "confirm-password").send_keys("Password1")
    browser.find_element(By.CSS_SELECTOR, ".auth-submit").click()
    wait.until(EC.url_contains("/login"))


def login_user(browser, live_server, identifier="student", password="Password1"):
    wait = WebDriverWait(browser, 5)
    browser.get(f"{live_server}/login")
    browser.find_element(By.ID, "login-identifier").send_keys(identifier)
    browser.find_element(By.ID, "login-password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, ".auth-submit").click()
    wait.until(EC.url_contains("/studybuddy"))
    wait.until(EC.presence_of_element_located((By.ID, "openCreateModal")))
