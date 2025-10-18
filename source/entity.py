from pydantic import BaseModel
from typing import Optional

class LinearInput(BaseModel):
    team: Optional[str] = None
    after: Optional[str] = None
    cycle: Optional[str] = None
    label: Optional[str] = None
    limit: Optional[int] = None
    query: Optional[str] = None
    state: Optional[str] = None
    before: Optional[str] = None
    orderBy: Optional[str] = None
    project: Optional[str] = None
    assignee: Optional[str] = None
    parentId: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    includeArchived: Optional[bool] = None

