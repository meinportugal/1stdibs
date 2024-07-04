import mysql.connector
from mysql.connector import Error
import requests
import csv
from collections import deque
import time
import datetime

start_timestamp = datetime.datetime.now()

# Подключение к базе данных MySQL
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='user',
            password='123',
            database='Categories_MP_Qty'
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Проверка существования категории
def check_category_exists(connection, category_path):
    start_time = time.time()
    
    conditions = []
    params = []
    
    for i, level in enumerate(category_path):
        if level is not None:
            conditions.append(f"categoryL{i+1} = %s")
            params.append(level)
        else:
            conditions.append(f"categoryL{i+1} IS NULL")
    
    query = f"""
    SELECT id FROM categories
    WHERE {' AND '.join(conditions)}
    """
    
    result = None
    cursor = None
    try:
        cursor = connection.cursor()
#        print(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        result = cursor.fetchone()
        print(f"Найден ID: {result[0] if result else None}. Категория {params}")
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        while cursor.nextset():  # Проверка что все результаты прочитаны
            pass
#    print(f'result is {result}')
    end_time = time.time()
    execution_time = end_time - start_time
    global total_check_category_exists_time
    total_check_category_exists_time += execution_time 
    return result[0] if result else None

# Создание новой категории
def create_category(connection, category_path, name):
    cursor = connection.cursor()
    query = """
    INSERT INTO categories (name, categoryL1, categoryL2, categoryL3, categoryL4, categoryL5, categoryL6)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, *category_path))
    connection.commit()
    category_id = cursor.lastrowid
    print(f"Создан ID {category_id}: {category_path}")
    cursor.close()
    return category_id

# Вставка записи о наличии товара
def insert_inventory_record(connection, category_id, available_quantity):
    cursor = connection.cursor()
    query = """
    INSERT INTO inventory_records (category_id, available_quantity, record_timestamp)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (category_id, available_quantity, start_timestamp))
    connection.commit()
    cursor.close()

# Шаблон API запроса
api_template = {
    "url": "https://www.1stdibs.com/soa/graphql/",
    "headers": {
        "Content-Type": "application/json"
    },
    "body": {
        "variables": {
            "userId": "",
            "personalizationId": "",
            "guestId": "h48ikrd0lxiddlf1pdns300y",
            "fetchUser": False,
            "fetchSb": True,
            "skipUser": False,
            "isTrade": False,
            "shouldFetchSponsoredItems": True,
            "includeSponsoredItems": True,
            "uriRef": "",
            "originalUrl": "",
            "first": 1,
            "page": 1,
            "localeOrigin": "https://www.1stdibs.com",
            "showSeller": True,
            "contentModuleId": "",
            "previewId": "",
            "regions": "EUROPEAN_UNION",
            "hasPersonalizedFilter": False,
            "userZipCode": "",
            "userCountryCode": "US",
            "fetchRegionalInfo": False,
            "disableForceFacet": True,
            "isClient": True,
            "disableNonParameterizedUrlRedirects": False,
            "fetchTileVideo": True,
            "interiorPhotosCount": 1,
            "priceBookName": "EU",
            "fetchAuctionsItemSearch": False,
            "regionsList": 'null',
            "pageDisplayEnum": "searchAndBrowse"
        },
        "id": "app-buyer-finding/463.0.0-2024-05-21T07:50:27.919Z/SbRespLayoutRefetchQuery"
    }
}

# Функция для отправки POST запроса и получения JSON ответа
def send_post_request(api_template, URL_category):
    start_time = time.time()
    body = api_template["body"]
    body["variables"]["uriRef"] = f"{URL_category}?abtests=sponsored-listings&devicetype=desktop&locale=en-US&pageSize=1"
    body["variables"]["originalUrl"] = URL_category
    retries = 5
    delay = 5  # Задержка перед повторной попыткой
    api_error_time = 0
    for attempt in range(retries):
        try:
            response = requests.post(api_template["url"], headers=api_template["headers"], json=body)
            response.raise_for_status()
            end_time = time.time()
            exec_time = end_time - start_time
            api_error_time = attempt * delay
            global total_api_error_delay_time
            total_api_error_delay_time += api_error_time
            global total_send_request_time
            total_send_request_time += exec_time

            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        
        if attempt < retries - 1:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    return None

# Функция для нахождения уровня категории и списка подкатегорий
def find_categories(json_data):
    filters = json_data.get("data", {}).get("viewer", {}).get("itemSearch", {}).get("filters", [])
    category_level = None
    subcategories = []

    for i in range(len(filters) - 1, -1, -1):
        filter_name = filters[i].get("name")
        if "categoryL" in filter_name:
            category_level = filter_name
            subcategory_values = filters[i].get("values", [])
            subcategories = [value.get("urlLabel") for value in subcategory_values]
            break

    return category_level, subcategories

# Функция для поиска начальных категорий
def get_start_categories(api_template):
    URL_category = "fashion"
    json_data = send_post_request(api_template, URL_category)
    if not json_data:
        return []

    filters = json_data.get("data", {}).get("viewer", {}).get("itemSearch", {}).get("filters", [])
    start_categories = []

    for i, filter_item in enumerate(filters):
        if filter_item.get("name") == "categoryL1":
            subcategory_values = filter_item.get("values", [])
            start_categories = [value.get("urlLabel") for value in subcategory_values]
            break

    return start_categories

# Основная функция для обхода категорий и подкатегорий
def crawl_categories(connection, start_url):
    category_queue = deque([(start_url, "")])
    visited_categories = set()

    while category_queue:
        current_category, parent_level = category_queue.popleft()
        if current_category in visited_categories:
            continue

        visited_categories.add(current_category)
        
        json_data = send_post_request(api_template, current_category)
        if not json_data:
            continue
        
        try:
            item_count = json_data.get("data", {}).get("viewer", {}).get("itemSearch", {}).get("totalResults", 0)
            name = json_data.get("data", {}).get("viewer", {}).get("itemSearch", {}).get("meta", {}).get("header", "")

            # Формируем путь категорий
            category_path = current_category.split('/')
            category_path.extend([None] * (6 - len(category_path)))  # Дополняем до 6 уровней

            category_id = check_category_exists(connection, category_path)
            if not category_id:
                category_id = create_category(connection, category_path, name)
            
            insert_inventory_record(connection, category_id, item_count)

            category_level, subcategories = find_categories(json_data)
            if subcategories and category_level != parent_level:
                for subcategory in subcategories:
                    category_queue.append((f"{current_category}/{subcategory}", category_level))
        
        except AttributeError as e:
            print(f"AttributeError: {e}")
            print(f"Error processing category: {current_category}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(f"Error processing category: {current_category}")

# Запуск скрипта
connection = create_connection()
# Глобальные переменные для хранения общего времени выполнения функций
total_send_request_time = 0
total_check_category_exists_time = 0
total_api_error_delay_time = 0
if connection:
    start_categories = get_start_categories(api_template)
    print(f"Найдены начальные категории: {start_categories}")

    start_time = time.time()
    for start_category in start_categories:
        crawl_categories(connection, start_category)
    end_time = time.time()
    print(f"Function 'crawl_categories' execution time: {end_time - start_time} seconds")
# Вывод общего времени выполнения функций
    print(f"Total 'total_send_request_time' execution time: {total_send_request_time} seconds")
    print(f"Total 'check_category_exists' execution time: {total_check_category_exists_time} seconds")
    print(f"Total 'total_api_error_delay_time' execution time: {total_api_error_delay_time} seconds")
    connection.close()
else:
    print("Не удалось подключиться к базе данных.")
    


