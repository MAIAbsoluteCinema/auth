from fastapi import FastAPI
import uvicorn

from models import RegisterRequest, LoginRequest, VerifyRequest
from firebase import register_user, login_user, verify_token

app = FastAPI()

@app.post("/register")
async def register(request: RegisterRequest):
    response = register_user(request.email, request.password, request.username)
    return response

@app.post("/login")
async def login(request: LoginRequest):
    response = login_user(request.email, request.password)
    return response

@app.post("/verify")
async def verify(request: VerifyRequest):
    response = verify_token(request.token)
    return response

@app.get("/test")
async def test():
    return {"message": "Server is working"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
