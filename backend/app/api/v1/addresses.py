from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressRead])
def list_addresses(db: Session = Depends(get_db), user = Depends(get_current_user)):
    rows = db.query(Address).filter(Address.user_id == user.id).order_by(Address.created_at.desc()).all()
    return [AddressRead.model_validate(r, from_attributes=True) for r in rows]


@router.post("/", response_model=AddressRead)
def create_address(payload: AddressCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if payload.is_default:
        db.query(Address).filter(Address.user_id == user.id, Address.kind == payload.kind, Address.is_default == True).update({Address.is_default: False})
    a = Address(user_id=user.id, **payload.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return AddressRead.model_validate(a, from_attributes=True)


@router.put("/{address_id}", response_model=AddressRead)
def update_address(address_id: int, payload: AddressUpdate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    a = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="address_not_found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        db.query(Address).filter(Address.user_id == user.id, Address.kind == a.kind, Address.is_default == True).update({Address.is_default: False})
    for k, v in data.items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return AddressRead.model_validate(a)


@router.delete("/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    a = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="address_not_found")
    db.delete(a)
    db.commit()
    return {"ok": True}