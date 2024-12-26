import psycopg2
from psycopg2 import sql
from firebase_admin import credentials, initialize_app, auth
import jwt as pyjwt
from datetime import datetime, timedelta
import requests
from fastapi import HTTPException

# Инициализация Firebase Admin SDK
cred = credentials.Certificate("service-account-key.json")
initialize_app(cred)

# Ваш Firebase API Key (из конфигурации)
FIREBASE_API_KEY = "AIzaSyCRkVpDEoq_ii589jj3bAMk_-78FTaAp10"  # Замените на ваш API ключ

# Секретный ключ для подписи JWT
SECRET_KEY = "your_secret_key"  # Замените на безопасный ключ

# Подключение к базе данных PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        dbname="your_db", user="your_user", password="your_password", host="localhost", port="5432"
    )
    return conn

# Функция для регистрации пользователя
def register_user(email, password, username):
    try:
        # Firebase REST API URL для регистрации пользователя
        firebase_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
         # Отправляем запрос на регистрацию
        response = requests.post(firebase_api_url, json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        })

        # Проверяем результат
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=response.json().get("error", {}).get("message", "Registration failed")
            )

        user_data = response.json()

        # Генерация пользовательского UUID
        user_id = user_data["localId"]  # UUID из Firebase
        role = "client"  # Роль по умолчанию

        # Сохранение в базе данных
        conn = get_db_connection()
        cursor = conn.cursor()

        # Вставка записи в таблицу conn_ids
        cursor.execute(
            sql.SQL("INSERT INTO conn_ids (firebase_id) VALUES (%s) RETURNING id"),
            [user_id]
        )
        conn.commit()
        db_id = cursor.fetchone()[0]  # Получаем сгенерированный id

        # Закрытие соединения с базой данных
        cursor.close()
        conn.close()

        # Генерация JWT токена с ролью, передаем id как строку
        payload = {
            "user": {
                "username": username,
                "id": db_id,  # Преобразуем id в строку
                "role": role,
            },
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=7),  # Токен истекает через 7 дней
        }

        token = pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token, "message": "User registered successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Функция для логина пользователя
def login_user(email, password):
    try:
        # Firebase REST API URL для проверки пароля
        firebase_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

        # Отправляем запрос на проверку email и пароля
        response = requests.post(firebase_api_url, json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        })

        # Проверяем результат
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail=response.json().get("error", {}).get("message", "Login failed")
            )

        user_data = response.json()
        user_id = user_data["localId"]

        # Получение числового id из базы данных по firebase_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL("SELECT id FROM conn_ids WHERE firebase_id = %s"),
            [user_id]
        )
        db_id = cursor.fetchone()

        if db_id is None:
            raise HTTPException(status_code=404, detail="User not found")

        db_id = db_id[0]  # Получаем id из базы данных

        # Закрытие соединения с базой данных
        cursor.close()
        conn.close()

        # Генерация JWT токена с ролью, передаем id как строку
        payload = {
            "user": {
                "username": email,  # Firebase не возвращает username
                "id": str(db_id),  # Преобразуем id в строку
                "role": "client",  # По умолчанию
            },
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=7),
        }

        token = pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token, "message": "Login successful!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Функция для проверки токена с добавленной проверкой роли
def verify_token(token: str):
    try:
        # Декодирование токена
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Проверяем, что роль пользователя - client
        if payload["user"]["role"] != "client":
            raise HTTPException(status_code=403, detail="User is not a client")

        # Возвращаем информацию о пользователе
        return {"isValid": True, "role": payload["user"]["role"], "user": payload["user"]}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
