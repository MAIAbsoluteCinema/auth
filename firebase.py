from firebase_admin import credentials, initialize_app, auth
import requests
from datetime import datetime, timedelta
import jwt as pyjwt
from fastapi import HTTPException

# Инициализация Firebase Admin SDK
cred = credentials.Certificate("123.json")
initialize_app(cred)

# Ваш Firebase API Key (из конфигурации)
FIREBASE_API_KEY = "AIzaSyCRkVpDEoq_ii589jj3bAMk_-78FTaAp10"  # Замените на ваш API ключ

# Секретный ключ для подписи JWT
SECRET_KEY = "your_secret_key"  # Замените на безопасный ключ

# Функция для регистрации пользователя
def register_user(email, password, username):
    try:
        # Создание пользователя в Firebase
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=username,
        )

        # Генерация пользовательского UUID
        user_id = user_record.uid  # UUID из Firebase
        role = "client"  # Роль по умолчанию

        # Генерация JWT токена с ролью
        payload = {
            "user": {
                "username": username,
                "id": user_id,
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

        # Генерация JWT токена с ролью
        payload = {
            "user": {
                "username": email,  # Firebase не возвращает username
                "id": user_data["localId"],  # ID пользователя
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
