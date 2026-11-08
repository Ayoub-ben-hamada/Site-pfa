from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str
    latest_version: str
    category: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    latest_version: str | None = None
    category: str | None = None


class ProductOut(ProductBase):
    id: int
