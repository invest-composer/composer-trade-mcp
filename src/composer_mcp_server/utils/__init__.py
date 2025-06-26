"""
Utility functions for Composer MCP Server.
"""

from .parsers import parse_stats, parse_dvm_capital, parse_backtest_output, epoch_to_date, epoch_ms_to_date

__all__ = [
    "parse_stats",
    "parse_dvm_capital", 
    "parse_backtest_output",
    "epoch_to_date",
    "epoch_ms_to_date"
]

def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to a maximum length.
    """
    return text[:max_length]
