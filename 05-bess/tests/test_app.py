"""Streamlit AppTest smoke tests (headless)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_default_runs():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    labels = [m.label for m in at.metric]
    assert "Extra IT under limit" in labels and "NPV" in labels and "BESS power needed" in labels
    assert len(at.tabs) == 7


def test_app_change_scenario_and_size():
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.selectbox(key="scen").select("saturated").run()
    assert not at.exception
    at.slider(key="e_mwh").set_value(40.0).run()
    assert not at.exception
    at.select_slider(key="resp").set_value(20).run()
    assert not at.exception
    assert any("Hybrid" in m.label for m in at.metric)
