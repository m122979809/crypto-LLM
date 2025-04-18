from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import re
import csv
chrome_driver_path = "C:\\Users\\M1229\\Downloads\\chromedriver-win64\\chromedriver.exe"
def scrape_coinday_data(chrome_driver_path, output_csv="output.csv"):
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    
    driver.get("https://coinday.cc/")
    time.sleep(5)
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    unique_titles = set()
    results = []

   
    title_elements  = soup.find_all(class_='Text')
    text_list = []
    
    for t in title_elements:
        inner_div = t.find('div') 
        if inner_div:
            text_list.append(inner_div.get_text(strip=True)) 

    date_pattern = re.compile(r'^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/\d{2}$')

    for i in range(len(text_list) - 2):
        youtuber = text_list[i]
        date = text_list[i + 1]
        title = text_list[i + 2]
        
        if date_pattern.match(date) and title not in unique_titles:
            unique_titles.add(title)  
            results.append((youtuber, date, title))


    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Youtuber", "Date", "Title"]) 
        writer.writerows(results)

    driver.quit()
    print(f"Data has been saved to {output_csv}")

if __name__ == '__main__':
    scrape_coinday_data(chrome_driver_path, output_csv='coinday.csv')