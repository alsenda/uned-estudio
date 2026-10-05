from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import store

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class NewPerson(BaseModel):
    name: str
    role: str | None = None
    subject: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str = ""


class UpdatePerson(BaseModel):
    name: str | None = None
    role: str | None = None
    subject: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class NewInteraction(BaseModel):
    title: str
    date: str | None = None
    channel: str | None = None
    detail: str = ""


@router.get("/people")
def get_people(role: str | None = None, subject: str | None = None, q: str | None = None):
    return store.list_people(role=role, subject=subject, q=q)


@router.post("/people")
def add_person(person: NewPerson):
    return store.create_person(
        name=person.name,
        role=person.role,
        subject=person.subject,
        email=person.email,
        phone=person.phone,
        notes=person.notes,
    )


@router.patch("/people/{person_id}")
def edit_person(person_id: str, person: UpdatePerson):
    try:
        return store.update_person(person_id, **person.model_dump(exclude_unset=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="persona no encontrada")


@router.delete("/people/{person_id}", status_code=204)
def remove_person(person_id: str):
    try:
        store.delete_person(person_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="persona no encontrada")


@router.get("/people/{person_id}/interactions")
def get_interactions(person_id: str):
    return store.list_interactions(person_id)


@router.post("/people/{person_id}/interactions")
def add_interaction(person_id: str, interaction: NewInteraction):
    return store.create_interaction(
        person_id=person_id,
        title=interaction.title,
        interaction_date=interaction.date,
        channel=interaction.channel,
        detail=interaction.detail,
    )


@router.delete("/interactions/{interaction_id}", status_code=204)
def remove_interaction(interaction_id: str):
    try:
        store.delete_interaction(interaction_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="interacción no encontrada")
