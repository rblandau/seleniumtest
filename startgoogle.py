import time
from selenium import webdriver
 
driver = webdriver.Firefox()
driver.get("http://www.google.com")

time.sleep(5)
driver.quit()
