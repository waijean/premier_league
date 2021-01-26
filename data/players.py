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

soup = BeautifulSoup(elem_html, "html")
table_html = soup.find('table')

# manual way
table_rows = table_html.find_all("tr")
data = []
for i, tr in enumerate(table_rows):
    # add the rest of td tags           )
    tds = tr.find_all('td')
    # skip the last column
    row = [td.text for td in tds[:-1]]

    # add href if exist (to exclude header row and intermediate header row)
    try:
        link = tds[0].find(href=True)["href"]
        row += [link]
        data.append(row)
    except (IndexError, TypeError):
       print(f"Skipping row {i}")

# first two rows are headers
header_0_list = [[th.text] * int(th["colspan"]) for th in table_rows[0].find_all('th', colspan=True)]
header_0 = [i for ls in header_0_list for i in ls] + [""]
# skip the first and last column
header_1 = [th.text for th in table_rows[1].find_all('th')][1:-1] + ["Player Link"]
header = [h1 if not h0 else h0 + " " + h1 for h0, h1 in zip(header_0, header_1)]
df = pd.DataFrame(data, columns=header)


df.to_csv("defense_stats.csv", index=False)