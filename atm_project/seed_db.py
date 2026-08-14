import mysql.connector
from werkzeug.security import generate_password_hash
import random
from datetime import datetime, timedelta

# Конфигурация БД
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Впишите пароль, если он есть
    'database': 'atm_db'
}

# Данные для генерации
users_data = [
    {"name": "Иванов Иван Иванович", "phone": "+79991112233", "balance": 50000.00, "card": "1111222233334444",
     "pin": "1234", "status": "active", "attempts": 0},
    {"name": "Петрова Анна Сергеевна", "phone": "+79992223344", "balance": 15500.00, "card": "2222333344445555",
     "pin": "0000", "status": "active", "attempts": 0},
    {"name": "Смирнов Алексей Ильич", "phone": "+79993334455", "balance": 8000.00, "card": "3333444455556666",
     "pin": "1111", "status": "active", "attempts": 1},
    {"name": "Кузнецова Елена Влад.", "phone": "+79994445566", "balance": 120500.00, "card": "4444555566667777",
     "pin": "7777", "status": "active", "attempts": 0},
    {"name": "Сидоров Михаил Андр.", "phone": "+79995556677", "balance": 300.00, "card": "5555666677778888",
     "pin": "5555", "status": "blocked", "attempts": 3}
]

trans_types = ['withdraw', 'deposit', 'balance_check']

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 1. Очистка старых данных (с отключением проверки ключей)
    print("Очистка старых данных...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE Transactions;")
    cursor.execute("TRUNCATE TABLE Cards;")
    cursor.execute("TRUNCATE TABLE Accounts;")
    cursor.execute("TRUNCATE TABLE Clients;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 2. Заполнение базы
    print("Генерация новых клиентов и карт...")
    for user in users_data:
        # Создаем клиента
        cursor.execute("INSERT INTO Clients (full_name, phone) VALUES (%s, %s)", (user['name'], user['phone']))
        client_id = cursor.lastrowid

        # Создаем счет
        cursor.execute("INSERT INTO Accounts (id_client, balance) VALUES (%s, %s)", (client_id, user['balance']))
        account_id = cursor.lastrowid

        # Создаем карту
        pin_hash = generate_password_hash(user['pin'])
        cursor.execute("""
            INSERT INTO Cards (id_account, card_number, pin_hash, status, failed_attempts) 
            VALUES (%s, %s, %s, %s, %s)
        """, (account_id, user['card'], pin_hash, user['status'], user['attempts']))
        card_id = cursor.lastrowid

        # 3. Генерируем историю транзакций
        num_transactions = random.randint(5, 12)
        current_time = datetime.now()

        for _ in range(num_transactions):
            t_type = random.choice(trans_types)
            # Сумма кратна 100 для снятия/пополнения, 0 для проверки баланса
            amount = 0 if t_type == 'balance_check' else random.randint(1, 50) * 100

            # Случайная дата за последние 30 дней
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            mins_ago = random.randint(0, 59)
            t_date = current_time - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)

            cursor.execute("""
                INSERT INTO Transactions (id_card, trans_type, amount, created_at) 
                VALUES (%s, %s, %s, %s)
            """, (card_id, t_type, amount, t_date.strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    print("База данных успешно заполнена.")
    print("ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ САЙТА:")
    print(f"{'Владелец':<25} | {'Номер карты':<18} | {'ПИН':<5} | {'Статус'}")

    for u in users_data:
        print(f"{u['name']:<25} | {u['card']:<18} | {u['pin']:<5} | {u['status']}")

except mysql.connector.Error as err:
    print(f"Ошибка БД: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()