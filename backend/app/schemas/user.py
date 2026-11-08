from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str
    organization: str


class UserCreate(UserBase):
    password: str = "demo123"
    products: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    organization: str | None = None
    products: list[int] | None = None


class UserOut(UserBase):
    id: int
    products: list[int] = Field(default_factory=list)


class PermissionUpdate(BaseModel):
    user_id: int
    product_id: int
    can_view: bool = True
    can_update: bool = True
    allowed_features: list[str] = Field(default_factory=list)
