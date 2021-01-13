from selenium import webdriver
from bs4 import BeautifulSoup

import pandas as pd

# include the path to compatible ChromeDriver version
driver = webdriver.Chrome("D:\chromedriver_win32\chromedriver.exe")
driver.get("https://fbref.com/en/comps/9/3232/schedule/2019-2020-Premier-League-Scores-and-Fixtures")


elem = driver.find_element_by_id("sched_ks_3232_1")
elem_html = elem.get_attribute("outerHTML")

soup = BeautifulSoup(elem_html, "html")
table_html = soup.find('table')

# shortcut with pandas
df = pd.read_html(str(table_html), flavor="bs4")[0]
df1 = df[df.Wk != "Wk"].dropna(how="all")


# manual way
table_rows = table_html.find_all("tr")
l = []
for i, tr in enumerate(table_rows):
    # week column has a th tag
    week = tr.find('th').text
    row = [week]

    # add the rest of td tags           )
    tds = tr.find_all('td')
    row += [td.text for td in tds]

    # add href if exist
    try:
        link = tds[-2].find(href=True)["href"]
        row[-2] = link
        l.append(row)
    except (IndexError, TypeError):
       print(f"Skipping row {i}")

header = [th.text for th in table_rows[0].find_all('th')]
df_manual = pd.DataFrame(l, columns=header)

# write to csv
df_manual.to_csv("1920PL_matches.csv", index=False)
driver.close()