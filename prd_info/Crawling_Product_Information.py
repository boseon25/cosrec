from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pyautogui
import csv
import pandas as pd
import Crawling_Product_Information_Preparation as CPI
import os

filepath = r'C:\Users\leeks\my_git\mango\prd_info\Set_default.txt' #User editable section
os.makedirs(os.path.dirname(filepath), exist_ok=True)  

# Dictionary storage function
def save_to_txt(filepath, variables):
    with open(filepath, 'w', encoding='utf-8') as f:
        for key, value in variables.items():
            f.write(f'{key}={value}\n')

# Load dictionary
variables = {}
with open(filepath, 'r', encoding='utf-8') as f:
    for line in f:
        if '=' in line:
            key, value = line.strip().split('=', 1)
            if value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except:
                    pass
            variables[key] = value

# Set variables
My_part = variables['item']
divide = int(variables['divide'])
Starting_point = [int(x) for x in str(variables.get('progress', '0-0')).split('-')]
if len(Starting_point) < 2:
    Starting_point += [0] * (2 - len(Starting_point))  # 항상 [카테고리, 분할] 형식

# Crawling function
def Collecting_data(My_part, divide, Starting_point=Starting_point):
    os.chdir(r'C:\Users\leeks\my_git\mango')  #User editable section
    files = os.listdir('url')
    os.chdir(r'C:\Users\leeks\my_git\mango\url')  #User editable section

    prd_dict = {}
    for fname in files:
        Temporary_list = []
        read_csv = pd.read_csv(fname)

        for j in range(len(read_csv)):
            Temporary_list.append(read_csv.iloc[j, 1])
            prd = read_csv.iloc[j, 0]

        prd_dict[prd] = Temporary_list

    Category_List = My_part.split('  ')
    Category_dict = {i: prd_dict[i] for i in Category_List}

    for k, v in Category_dict.items():
        Divided_list = CPI.split_list_equally(v, divide)
        Category_dict[k] = Divided_list

    keys_list = list(Category_dict.keys())
    start_key_index, start_value_index = Starting_point

    component_dataset = []
    info_dataset = pd.DataFrame(columns=['제품명', '가격', '사용기한', '사용방법', '큰카테고리', '작은카테고리'])

    for ki, k in enumerate(keys_list):
        if ki < start_key_index:
            continue

        v_list = Category_dict[k]
        for vi, v in enumerate(v_list):
            if ki == start_key_index and vi < start_value_index:
                continue

            for url in v:
                try:
                    html = CPI.fetch_full_html(url)
                    info, ingredient = CPI.parse_product_info(html, k)

                    # Check the number of columns
                    if isinstance(info, (list, tuple)) and len(info) == len(info_dataset.columns):
                        info_dataset.loc[len(info_dataset)] = info
                    else:
                        print(f"[경고] info 컬럼 수 불일치 → URL: {url}, info: {info}")
                        continue

                    component_dataset.append(ingredient)

                except Exception as e:
                    print(f"[오류] URL 처리 중 예외 발생 → {url}")
                    print(f"[에러 메시지] {e}")
                    continue  

            # 수동 종료 여부 확인
            stop = input('stop? [Y/N]').strip().lower()
            if stop == 'y':
                variables['progress'] = f"{ki}-{vi + 1}"
                save_to_txt(filepath, variables)
                print(f"[수동종료] 진행 상황 저장됨: {ki}-{vi + 1}")
                return info_dataset, component_dataset
    
    variables['progress'] = f"{ki+1}-0"
    save_to_txt(filepath, variables)
    print(f"[자동종료] 진행 상황 저장됨: {ki+1}-0")
    return info_dataset, component_dataset

# 실행
info_dataset, component_dataset = Collecting_data(My_part, divide)

# 결과 저장 (덮어쓰기 아님, 이어쓰기)
info_dataset.to_csv(r'C:\Users\leeks\OneDrive\바탕 화면\csv\Product_Information.csv', index=False, mode='a', header=False) #User editable section
pd.DataFrame(component_dataset).to_csv(r'C:\Users\leeks\OneDrive\바탕 화면\csv\Ingredients_list.csv', index=False, mode='a', header=False)  #User editable section