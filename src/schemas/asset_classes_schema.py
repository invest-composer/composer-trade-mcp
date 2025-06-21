"""
Schema for asset classes used in symphony creation.
"""
from typing import List, Literal
from pydantic import BaseModel, Field, validator

AssetClass = Literal["EQUITIES", "CRYPTO"]

class AssetClasses(BaseModel):
    """
    Schema for asset classes that can be used in symphony creation.
    Must contain at least one of EQUITIES or CRYPTO, and no more than one of each.
    """
    classes: List[AssetClass] = Field(
        min_items=1,
        max_items=2,
        description="List of asset classes to use in symphony creation"
    )

    @validator("classes")
    def validate_unique_classes(cls, v):
        """Ensure no duplicate asset classes are present."""
        if len(set(v)) != len(v):
            raise ValueError("Duplicate asset classes are not allowed")
        return v

    @validator("classes")
    def validate_asset_classes(cls, v):
        """Ensure only valid asset classes are present."""
        valid_classes = {"EQUITIES", "CRYPTO"}
        invalid_classes = set(v) - valid_classes
        if invalid_classes:
            raise ValueError(f"Invalid asset classes: {invalid_classes}")
        return v 