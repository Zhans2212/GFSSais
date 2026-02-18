from pydantic import BaseModel

class User(BaseModel):
    username: str
    fio: str
    dep_name: str
    post: str
    rfbn_id: str | None = None
    roles: list[str] = []
    top_control: int = 0
