from pydantic import BaseModel, Field
from typing import Optional


class AddressCreate(BaseModel):
    kind: str = Field(pattern="^(shipping|billing)$")
    name: str
    street: str
    city: str
    province: str
    zip_code: str
    country: str = "AR"
    phone: Optional[str] = None
    is_default: bool = False


class AddressRead(BaseModel):
    id: int
    kind: str
    name: str
    street: str
    city: str
    province: str
    zip_code: str
    country: str
    phone: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True


class AddressUpdate(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_default: Optional[bool] = None