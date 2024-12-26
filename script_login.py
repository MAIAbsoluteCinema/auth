import requests

url = "http://127.0.0.1:8080/login" 
data = {
    "email": "1234567111111@example.com",   # Замените на email пользователя
    "password": "ruslan123"   # Замените на пароль пользователя
}

# Отправка POST запроса на сервер FastAPI
response = requests.post(url, json=data)

# Вывод ответа от сервера
if response.status_code == 200:
    print("Login successful!")
    print("Response:", response.json())
else:
    print("Login failed!")
    print("Error:", response.json())
