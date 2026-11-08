from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserMe(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    organization: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe
