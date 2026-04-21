"""Classification: heuristic classifier + competitor detection."""

from __future__ import annotations

from src.classification import CompetitorDetector, HeuristicClassifier
from src.models import CompetitorTool, FormType

_INTERCOM_SNIPPET = """
<html>
<head>
  <script async src="https://widget.intercom.io/widget/abc123"></script>
</head>
<body><h1>Contact us</h1></body>
</html>
"""

_CALENDLY_SNIPPET = """
<html>
<head>
  <link rel="stylesheet" href="https://assets.calendly.com/assets/external/widget.css">
</head>
<body><div id="schedule"></div></body>
</html>
"""

_CONTACT_FORM_SNIPPET = """
<html>
<body>
  <h2>Contact</h2>
  <form class="contact-form" method="post">
    <input type="text" name="name">
    <input type="email" name="email">
    <input type="tel" name="phone">
    <textarea name="msg"></textarea>
    <button>Send</button>
  </form>
</body>
</html>
"""

_PLAIN_HTML = "<html><body><h1>About us</h1><p>We are a local business.</p></body></html>"


def test_heuristic_detects_chat_widget() -> None:
    classifier = HeuristicClassifier()
    assert classifier.classify(_INTERCOM_SNIPPET, url="https://x") == FormType.CHAT_WIDGET


def test_heuristic_detects_booking_widget() -> None:
    classifier = HeuristicClassifier()
    assert classifier.classify(_CALENDLY_SNIPPET, url="https://x") == FormType.BOOKING_WIDGET


def test_heuristic_detects_contact_form() -> None:
    classifier = HeuristicClassifier()
    assert classifier.classify(_CONTACT_FORM_SNIPPET, url="https://x") == FormType.CONTACT_FORM


def test_heuristic_returns_none_when_no_form() -> None:
    classifier = HeuristicClassifier()
    assert classifier.classify(_PLAIN_HTML, url="https://x") == FormType.NONE


def test_competitor_detector_finds_intercom() -> None:
    assert CompetitorDetector().detect(_INTERCOM_SNIPPET) == [CompetitorTool.INTERCOM]


def test_competitor_detector_finds_calendly() -> None:
    assert CompetitorDetector().detect(_CALENDLY_SNIPPET) == [CompetitorTool.CALENDLY]


def test_competitor_detector_finds_multiple_tools() -> None:
    mixed = _INTERCOM_SNIPPET + _CALENDLY_SNIPPET
    detected = CompetitorDetector().detect(mixed)
    assert CompetitorTool.INTERCOM in detected
    assert CompetitorTool.CALENDLY in detected


def test_competitor_detector_empty_on_clean_page() -> None:
    assert CompetitorDetector().detect(_PLAIN_HTML) == []
