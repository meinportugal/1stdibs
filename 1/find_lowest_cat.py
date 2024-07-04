import mysql.connector

def get_lowest_categories():
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host='localhost',
            user='user',
            password='123',
            database='Categories_MP_Qty'
        )
        cursor = conn.cursor(dictionary=True)

        # SQL-запрос для получения всех категорий
        query = """
        SELECT id, categoryL1, categoryL2, categoryL3, categoryL4, categoryL5, categoryL6
        FROM categories
        """
        cursor.execute(query)

        # Получение результатов
        categories = cursor.fetchall()

        # Создаем словарь для хранения категорий
        category_dict = {}

        # Заполняем словарь
        for category in categories:
            path = []
            for level in ['categoryL1', 'categoryL2', 'categoryL3', 'categoryL4', 'categoryL5', 'categoryL6']:
                if category[level]:
                    path.append(category[level])
                else:
                    break
            path_str = '/'.join(path)
            category_dict[path_str] = category['id']

        # Находим самые глубокие категории
        lowest_categories = []
        for path, id in category_dict.items():
            is_lowest = True
            for other_path in category_dict.keys():
                if path != other_path and other_path.startswith(path + '/'):
                    is_lowest = False
                    break
            if is_lowest and '/' in path:  # Убеждаемся, что это не категория верхнего уровня
                lowest_categories.append(path)

        # Вывод результатов
        for category_path in lowest_categories:
            print(category_path)

        return lowest_categories

    except mysql.connector.Error as err:
        print(f"Ошибка при работе с базой данных: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    get_lowest_categories()
