"""set_macro_targets / get_fixed_macro_targets over /api/v2/set_pref."""

from __future__ import annotations

import pytest
from test_client import make_cold_client

from cronometer_api_mcp.client import CronometerError

OK = {"result": "SUCCESS", "messages": []}


def profile(**prefs) -> dict:
    base = {
        "targets.fixed.protein": "151.0",
        "targets.fixed.protein.max": "151.0",
        "targets.fixed.fats": "143.0",
        "targets.fixed.fats.max": "143.0",
        "targets.fixed.net.carbs": "30.0",
        "targets.fixed.net.carbs.max": "30.0",
        "weightGoal": "-1.0",
        "weightUnit": "Pounds",
    }
    base.update(prefs)
    return {"result": "SUCCESS", "prefs": [{k: v} for k, v in base.items()]}


def test_get_fixed_macro_targets_reads_prefs(tmp_path):
    client, _ = make_cold_client(tmp_path, [profile()])
    assert client.get_fixed_macro_targets() == {
        "protein_g": 151.0,
        "fat_g": 143.0,
        "net_carbs_g": 30.0,
        "weight_goal_per_week": -1.0,
        "weight_unit": "Pounds",
    }


def test_set_macro_targets_writes_value_and_max_then_reads_back(tmp_path):
    after = profile(
        **{
            "targets.fixed.protein": "160.0",
            "targets.fixed.protein.max": "160.0",
            "weightGoal": "-1.5",
        }
    )
    client, state = make_cold_client(tmp_path, [OK, OK, OK, after, after])

    result = client.set_macro_targets(protein_g=160, weight_goal_per_week=-1.5)

    sets = [(p["key"], p["val"]) for p in state["payloads"] if "key" in p]
    assert sets == [
        ("targets.fixed.protein", "160.0"),
        ("targets.fixed.protein.max", "160.0"),
        ("weightGoal", "-1.5"),
    ]
    assert result["protein_g"] == 160.0
    assert result["fat_g"] == 143.0
    assert result["weight_goal_per_week"] == -1.5


def test_set_macro_targets_raises_when_value_does_not_stick(tmp_path):
    client, _ = make_cold_client(tmp_path, [OK, OK, profile()])
    with pytest.raises(CronometerError, match="did not read back"):
        client.set_macro_targets(fat_g=90)


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"protein_g": -1}, {"net_carbs_g": 5000}, {"weight_goal_per_week": -3}],
)
def test_set_macro_targets_rejects_bad_input_without_calls(tmp_path, kwargs):
    client, state = make_cold_client(tmp_path, [OK])
    with pytest.raises(CronometerError):
        client.set_macro_targets(**kwargs)
    assert state["payloads"] == []
