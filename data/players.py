from selenium import webdriver
from bs4 import BeautifulSoup

import pandas as pd

# include the path to compatible ChromeDriver version
driver = webdriver.Chrome("D:\chromedriver_win32\chromedriver.exe")
driver.get("https://fbref.com/en/comps/9/defense/Premier-League-Stats")

# disagree privacy
buttons = driver.find_element_by_class_name("qc-cmp2-summary-buttons")
buttons_list = buttons.find_elements_by_tag_name("button")

for button in buttons_list:
    if button.text == "DISAGREE":
        button.click()
        break

# convert to per 90
button = driver.find_element_by_id("stats_defense_per_match_toggle")
button.click()

# get the defense stats tables
elem = driver.find_element_by_id("div_stats_defense")
elem_html = elem.get_attribute("outerHTML")

df = pd.read_html(str(elem_html), flavor="bs4")[0]

df.to_csv("defense_stats.csv", index=False)