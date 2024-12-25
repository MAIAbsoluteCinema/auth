import requests

url = "http://127.0.0.1:8080/register" 
data = {
    "email": "ruslan@example.com",
    "password": "ruslan123",
    "username": "xxxd"
}
response = requests.post(url, json=data)

if response.status_code == 201:  # Статус 201 означает успешную регистрацию
    print("Registration successful!")
    print("Response:", response.json())
else:
    print("Registration failed!")
    print("Error:", response.json())
