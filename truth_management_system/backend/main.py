from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import openai

app = FastAPI()

# Mock database for demonstration purposes
users_db = {}
resources_db = {}

class User(BaseModel):
    username: str
    password: str

class Resource(BaseModel):
    resource_id: int
    type: str
    allocated_to: str

@app.post("/user/register")
async def register_user(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    users_db[user.username] = user.password
    return {"message": "User registered successfully"}

@app.post("/user/login")
async def login_user(user: User):
    if user.username not in users_db or users_db[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "token": f"token_{user.username}"}

@app.post("/resource/allocate")
async def allocate_resource(resource: Resource, token: str = Depends(lambda request: request.headers.get("Authorization"))):
    if not token or not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    resource_id = len(resources_db) + 1
    resources_db[resource_id] = resource.dict()
    return {"message": "Resource allocated successfully", "resource_id": resource_id}

@app.get("/resource/list")
async def list_resources(token: str = Depends(lambda request: request.headers.get("Authorization"))):
    if not token or not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"resources": list(resources_db.values())}

@app.post("/llm/generate")
async def generate_text(prompt: str, token: str = Depends(lambda request: request.headers.get("Authorization"))):
    if not token or not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    return {"generated_text": response.choices[0].text.strip()}
