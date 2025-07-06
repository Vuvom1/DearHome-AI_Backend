from fastapi import APIRouter, Depends, HTTPException, WebSocket, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from typing import Optional
import os
# Import necessary libraries
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Set up OAuth2 with Password flow (token URL is where client gets token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Your secret key and algorithm settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ISSUER = os.getenv("JWT_ISSUER", "http://localhost:5000/")
AUDIENCE = os.getenv("JWT_AUDIENCE", "http://localhost:5000/")
# Ensure SECRET_KEY is set

ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the received token
        payload = jwt.decode(token, SECRET_KEY, issuer=ISSUER, audience=AUDIENCE, algorithms=[ALGORITHM])
        username: str = payload.get("unique_name")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:  
        raise credentials_exception 
        
    # Get the user from database or other storage
    # user = get_user(username)
    # if user is None:
    #     raise credentials_exception
    
    return username  # or return user object

async def get_token_from_websocket(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token is required for authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required for authentication",
        )
    
    return token

async def get_current_user_ws(websocket: WebSocket, token: str = Depends(get_token_from_websocket)):
    try:
        payload = jwt.decode(token, SECRET_KEY, issuer=ISSUER, audience=AUDIENCE, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")  # Debugging line to check the payload
        user_id: str = payload.get("nameid")
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token is invalid or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
            )
        return user_id
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token is invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired"
        )