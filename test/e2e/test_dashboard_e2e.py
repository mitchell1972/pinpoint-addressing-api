import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

DEMO_KEY = "pk_test_pinpoint_demo_0001"


def test_dashboard_search_flow(live_server, page):
    """A dispatcher opens the dashboard, saves their key, searches, sees a result."""
    page.goto(f"{live_server}/dashboard/")

    page.get_by_test_id("api-key").fill(DEMO_KEY)
    page.get_by_test_id("save-key").click()
    expect(page.get_by_test_id("key-status")).to_have_text("saved")

    page.get_by_test_id("search-input").fill("silverbird galleria ahmadu bello way")
    page.get_by_test_id("search-btn").click()

    # The Victoria Island address comes back as the top result.
    expect(page.get_by_test_id("results")).to_contain_text("PIN-VIC-002")
    expect(page.get_by_test_id("results")).to_contain_text("Silverbird")


def test_dashboard_record_delivery_and_analytics(live_server, page):
    """Record a delivery, then load analytics and see it reflected."""
    page.goto(f"{live_server}/dashboard/")
    page.get_by_test_id("api-key").fill(DEMO_KEY)
    page.get_by_test_id("save-key").click()

    page.get_by_test_id("del-code").fill("PIN-VIC-002")
    page.get_by_test_id("del-status").select_option("delivered")
    page.get_by_test_id("record-btn").click()
    expect(page.get_by_test_id("record-status")).to_have_text("recorded")

    page.get_by_test_id("load-analytics").click()
    expect(page.get_by_test_id("summary")).to_contain_text("delivered 1")
