from pydantic import BaseModel
from typing import Optional

class LinearInput(BaseModel):
    after: Optional[str] = None
    limit: Optional[int] = None
    before: Optional[str] = None
    orderBy: Optional[str] = None

