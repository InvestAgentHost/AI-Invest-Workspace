"""SEC EDGAR native HTML source acquisition for 10-K filings."""

from .execution import build_sec_html_plan, execute_sec_html_plan
from .pipeline import execute_sec_html

__all__ = ["build_sec_html_plan", "execute_sec_html", "execute_sec_html_plan"]
