
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Operation(BaseModel):
    operation_type: Literal["DEPOSIT", "WITHDRAW"]
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
