import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_checkout_widget_select_flow(live_server, page):
    """A shopper types an address, picks a suggestion, and the host page receives
    the verified token."""
    page.goto(f"{live_server}/widget/demo.html")

    page.get_by_test_id("pp-input").fill("silverbird galleria ahmadu bello way")

    # Type-ahead suggestions appear; pick the first.
    first = page.get_by_test_id("pp-suggestion").first
    first.wait_for()
    first.click()

    # The widget hands the merchant page a verified token (the address code).
    expect(page.get_by_test_id("host-token")).to_contain_text("PIN-VIC-002")
    expect(page.get_by_test_id("pp-selected")).to_contain_text("PIN-VIC-002")
