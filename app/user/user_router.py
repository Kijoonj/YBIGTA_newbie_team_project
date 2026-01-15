from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    Register a new user in the system.
    
    """
    try:
        new_user = service.register_user(user)
        return BaseResponse(status="success", data=new_user, message="User registration success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    Delete a user account based on the provided email.
    
    Returns the deleted user's data. Raises a 404 error if the user 
    to be deleted is not found.
    """
    
    try:
        deleted_user = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=deleted_user, message="User Deletion Success.") 
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    Update the password for an existing user.
    
    Identifies the user by email and updates their password. Raises a 404 error 
    if the user is not found.
    """
    try:
        update_user_password = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data= update_user_password, message="User password update success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
