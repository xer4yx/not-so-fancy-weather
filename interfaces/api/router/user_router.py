from fastapi import APIRouter, Depends, Query, Request, Body
from core.services import UserService
from interfaces.api.di import get_user_service

user_router = APIRouter(prefix="/v1", tags=["users"])

@user_router.post(path="/user")
async def create_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    username: str = Body(description="Username"),
    email: str = Body(description="Email"),
    password: str = Body(description="Password")):
    return user_service.create_user(username=username, email=email, password=password)

@user_router.get(path="/user")
async def read_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    return user_service.read_user(key=key, value=value)

@user_router.put(path="/user")
async def update_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value"),
    data: dict = Body(description="Data")):
    return user_service.update_user(key=key, id=value, data=data)

@user_router.delete(path="/user")
async def delete_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    return user_service.delete_user(key=key, id=value)