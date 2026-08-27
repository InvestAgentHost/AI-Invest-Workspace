"""Versioned ResearchFoundry source binding instances."""

import json
from importlib.resources import files

from research_foundry.preprocessing.contracts import SourceBinding


TEN_K_SEC_HTML_V1 = "ten_k_sec_html.v1.json"


def load_ten_k_sec_html_v1() -> SourceBinding:
    """Load and validate the SEC EDGAR native HTML source binding."""

    binding_path = files(__package__).joinpath(TEN_K_SEC_HTML_V1)
    payload = json.loads(binding_path.read_text(encoding="utf-8"))
    return SourceBinding.model_validate(payload)


__all__ = ["load_ten_k_sec_html_v1"]
