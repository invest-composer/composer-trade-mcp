from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class AccountHoldingResponse(BaseModel):
    ticker: str
    quantity: float

class AccountResponse(BaseModel):
    account_uuid: UUID
    account_foreign_id: str
    account_type: str
    asset_classes: List[str]
    account_number: str
    status: str
    broker: str
    created_at: datetime
    first_deposit_at: Optional[datetime] = None
    first_incoming_acats_transfer_at: Optional[datetime] = None
    first_deploy_at: Optional[datetime] = None
    first_position_created_at: Optional[datetime] = None
    has_queued_deploy: bool = False
    has_active_position: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "account_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "account_foreign_id": "string",
                "account_type": "string", 
                "asset_classes": ["CRYPTO"],
                "account_number": "string",
                "status": "string",
                "broker": "string",
                "created_at": "2024-03-20T00:00:00Z",
                "first_deposit_at": None,
                "first_incoming_acats_transfer_at": None,
                "first_deploy_at": None,
                "first_position_created_at": None,
                "has_queued_deploy": False,
                "has_active_position": False
            }
        }

class PortfolioStatsResponse(BaseModel):
    portfolio_value: float
    total_cash: float
    pending_deploys_cash: float
    total_unallocated_cash: float
    net_deposits: float
    simple_return: float
    todays_percent_change: float
    todays_dollar_change: float
