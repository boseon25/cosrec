from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

#html parsing
def fetch_full_html(url, output_path="full_page.html"):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(15)  
        html = driver.page_source

        return html

    finally:
        driver.quit()

#Find product information and product name
def parse_product_info(html, Category):
    wanted_keys = [
        "사용기한(또는 개봉 후 사용기간)",
        "사용방법",
        "화장품법에 따라 기재해야 하는 모든 성분"
    ]

    soup = BeautifulSoup(html, "html.parser")
    
    #Product Information
    product_info = {}
    for dl in soup.select("#artcInfo dl.detail_info_list"):
        dt = dl.find("dt")
        dd = dl.find("dd")
        if dt and dd:
            title = dt.get_text(strip=True)
            content = dd.get_text(" ", strip=True)
            product_info[title] = content
    
    final_info = []
    Product_Ingredients = []
    #Product name
    product_name = soup.find("p", class_="prd_name").text.strip()
    final_info.append(product_name)
    Product_Ingredients.append(product_name)

    #Product price
    price_tag = soup.find("span", class_="price-2").find('strong')
    price = price_tag.get_text().replace(',', '').strip()
    final_info.append(price)

    #Change to desired format
    for key in wanted_keys:
        if key in product_info:
            if key == "화장품법에 따라 기재해야 하는 모든 성분":
                # Split the ingredients by comma and remove any extra spaces
                ingredients = [ingredient.strip() for ingredient in product_info[key].split(",")]
                for i in ingredients:
                    Product_Ingredients.append(i)
            else:
                final_info.append(product_info[key])
        else:
            final_info.append("정보 없음")  # Default value if key not found
    for i in Category.split('_'):
        final_info.append(i)

    return final_info, Product_Ingredients

def split_list_equally(lst, n):
        k, m = divmod(len(lst), n)
        return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]