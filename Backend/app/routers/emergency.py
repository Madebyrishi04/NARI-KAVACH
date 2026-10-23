
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.emergency_contact import EmergencyContact
from app.schemas.emergency_contact import (
    EmergencyContactCreate,
    EmergencyContactResponse
)
from app.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/emergency-contacts",
    tags=["Emergency Contacts"]
)


@router.post(
    "/",
    response_model=EmergencyContactResponse,
    status_code=status.HTTP_201_CREATED
)
def add_emergency_contact(
    contact_data: EmergencyContactCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_contact = EmergencyContact(
        user_id=user_id,
        contact_name=contact_data.contact_name,
        phone_number=contact_data.phone_number,
        email=contact_data.email,
        relationship=contact_data.relationship
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


@router.get("/", response_model=list[EmergencyContactResponse])
def get_emergency_contacts(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).all()

    return contacts


@router.put(
    "/{contact_id}",
    response_model=EmergencyContactResponse
)
def update_emergency_contact(
    contact_id: int,
    contact_data: EmergencyContactCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == user_id
    ).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )

    contact.contact_name = contact_data.contact_name
    contact.phone_number = contact_data.phone_number
    contact.email = contact_data.email
    contact.relationship = contact_data.relationship

    db.commit()
    db.refresh(contact)

    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_emergency_contact(
    contact_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == user_id
    ).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )

    db.delete(contact)
    db.commit()

    return None
