from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import store

router = APIRouter(prefix="/api/agenda", tags=["agenda"])


class NewEvent(BaseModel):
    title: str
    date: str
    time: str | None = None
    type: str = "otro"
    subject: str | None = None
    links: list[str] | None = None
    description: str = ""


class UpdateEvent(BaseModel):
    title: str | None = None
    date: str | None = None
    time: str | None = None
    type: str | None = None
    subject: str | None = None
    links: list[str] | None = None
    description: str | None = None


class NewTodo(BaseModel):
    title: str
    due_date: str | None = None
    subject: str | None = None
    links: list[str] | None = None
    description: str = ""


class UpdateTodo(BaseModel):
    title: str | None = None
    due_date: str | None = None
    subject: str | None = None
    links: list[str] | None = None
    description: str | None = None
    done: bool | None = None


@router.get("/events")
def get_events(start: str | None = None, end: str | None = None, subject: str | None = None):
    return store.list_events(start=start, end=end, subject=subject)


@router.post("/events")
def add_event(event: NewEvent):
    return store.create_event(
        title=event.title,
        date_=event.date,
        time=event.time,
        type_=event.type,
        subject=event.subject,
        links=event.links,
        description=event.description,
    )


@router.patch("/events/{event_id}")
def edit_event(event_id: str, event: UpdateEvent):
    try:
        return store.update_event(event_id, **event.model_dump(exclude_unset=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="evento no encontrado")


@router.delete("/events/{event_id}", status_code=204)
def remove_event(event_id: str):
    try:
        store.delete_event(event_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="evento no encontrado")


@router.get("/todos")
def get_todos(done: bool | None = None, subject: str | None = None):
    return store.list_todos(done=done, subject=subject)


@router.post("/todos")
def add_todo(todo: NewTodo):
    return store.create_todo(
        title=todo.title,
        due_date=todo.due_date,
        subject=todo.subject,
        links=todo.links,
        description=todo.description,
    )


@router.patch("/todos/{todo_id}")
def edit_todo(todo_id: str, todo: UpdateTodo):
    try:
        return store.update_todo(todo_id, **todo.model_dump(exclude_unset=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="tarea no encontrada")


@router.delete("/todos/{todo_id}", status_code=204)
def remove_todo(todo_id: str):
    try:
        store.delete_todo(todo_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="tarea no encontrada")
