from pydantic import BaseModel
from typing import List, Optional

class EvidenceBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str

class EvidenceCreate(EvidenceBase):
    pass

class Evidence(EvidenceBase):
    id: int

class EvidenceList(BaseModel):
    items: List[Evidence]
    total: int

class AuditLogBase(BaseModel):
    action: str
    timestamp: str

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int

class AuditLogList(BaseModel):
    items: List[AuditLog]
    total: int