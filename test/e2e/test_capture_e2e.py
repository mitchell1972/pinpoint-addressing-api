import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

DEMO_KEY = "pk_test_pinpoint_demo_0001"


def test_offline_capture_then_deferred_sync(live_server, page, context):
    """Capture two locations while offline, then sync once back online."""
    page.goto(f"{live_server}/capture/")
    page.get_by_test_id("api-key").fill(DEMO_KEY)
    page.get_by_test_id("save-key").click()

    context.set_offline(True)  # no signal — capture must still work
    for lat, lng in (("6.50", "3.36"), ("6.51", "3.37")):
        page.get_by_test_id("cap-lat").fill(lat)
        page.get_by_test_id("cap-lng").fill(lng)
        page.get_by_test_id("cap-landmark").fill(f"Offline shop {lat}")
        page.get_by_test_id("queue-btn").click()
    expect(page.get_by_test_id("queue-count")).to_have_text("2")

    context.set_offline(False)  # back online — deferred sync
    page.get_by_test_id("sync-btn").click()
    expect(page.get_by_test_id("sync-status")).to_contain_text("synced 2")
    expect(page.get_by_test_id("queue-count")).to_have_text("0")
    expect(page.get_by_test_id("sync-results")).to_contain_text("created")
