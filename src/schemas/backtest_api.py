from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import date

class LegendEntry(BaseModel):
    """Schema for a legend entry that maps a ticker/symbol ID to a display name."""
    name: str = Field(..., description="Display name for the ticker/symbol")

DvmCapitalEntry = Dict[int, float]
DvmCapital = Dict[str, DvmCapitalEntry]
Legend = Dict[str, LegendEntry]

class ParsedDailyValue(BaseModel):
    """Schema for a single parsed daily value row."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    # Additional fields will be dynamically added based on the tickers in the data

class ParsedDailyValues(BaseModel):
    """Schema for the parsed daily values returned by parse_dvm_capital."""
    values: List[ParsedDailyValue] = Field(..., description="List of daily value rows")

class BacktestResponse(BaseModel):
    """Schema for the response from the backtest API."""
    data_warnings: Optional[Dict[str, List[Dict[str, str]]]] = Field(None, description="List of data warnings")
    first_day: Optional[int] = Field(None, description="First day of the backtest")
    capital: Optional[float] = Field(None, description="Initial capital of the backtest")
    last_market_day: Optional[int] = Field(None, description="Last market day of the backtest")
    last_market_days_holdings: Optional[Dict[str, float]] = Field(None, description="Last market days shares of the backtest")
    last_market_days_value: Optional[float] = Field(None, description="Last market days value of the backtest")
    stats: Optional[Dict] = Field(None, description="Stats of the backtest")
    dvm_capital: Optional[DvmCapital] = Field(None, description="DVM capital of the backtest")
    legend: Optional[Legend] = Field(None, description="Legend of the backtest")