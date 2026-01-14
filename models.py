"""Auto-generated DataFlow models from database schema."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from dataflow import DataFlow

# Initialize DataFlow instance
db = DataFlow()


@db.model
class User:
    """Model for users table."""

    name: str
    email: str
    created_at: datetime
    # orders = db.has_many("orders", "user_id")


@db.model
class Order:
    """Model for orders table."""

    user_id: int
    total: Decimal
    status: Optional[str] = "pending"
    # user = db.belongs_to("user", "user_id")
