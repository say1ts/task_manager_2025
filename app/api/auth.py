from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import UserLogin
from app.auth.schemas import UserCreate, UserResponse, Token
from app.auth.service import UserAlreadyExistsError, InvalidCredentialsError
from app.auth.dependencies import AuthServiceDep, CurrentUser

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user: UserCreate, service: AuthServiceDep):
    try:
        return await service.register_user(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    service: AuthServiceDep, form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = await service.authenticate_user(
            UserLogin(email=form_data.username, password=form_data.password)
        )
        access_token = service.create_access_token(data={"sub": user.email})
        return Token(access_token=access_token, token_type="bearer")
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user
