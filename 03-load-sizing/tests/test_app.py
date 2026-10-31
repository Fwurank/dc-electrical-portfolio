"""Streamlit AppTest smoke tests (headless)."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_default_runs():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    labels = [m.label for m in at.metric]
    assert "Campus demand" in labels and "MSB I''k (IEC 60909)" in labels
    assert len(at.tabs) == 6


def test_app_switch_scheme_and_target_pue():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.selectbox(key="scheme").select("2N").run()
    assert not at.exception
    at.radio(key="pue_mode").set_value("Target hall pPUE").run()
    assert not at.exception
    at.selectbox(key="scheme").select("BR").run()
    assert not at.exception
    assert any("catcher" in i.value for i in at.info)
