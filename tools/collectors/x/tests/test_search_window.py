from __future__ import annotations

from x.collectors.browser import _search_is_empty


class _Body:
    def __init__(self, text: str) -> None:
        self.text = text

    def inner_text(self, timeout: int) -> str:
        assert timeout == 2000
        return self.text


class _Page:
    def __init__(self, text: str) -> None:
        self.text = text

    def locator(self, selector: str) -> _Body:
        assert selector == "body"
        return _Body(self.text)


def test_search_empty_detection_handles_english_and_chinese() -> None:
    assert _search_is_empty(_Page("No results for from:Example"))
    assert _search_is_empty(_Page("没有结果"))
    assert not _search_is_empty(_Page("Herman Jin\n帖子"))
