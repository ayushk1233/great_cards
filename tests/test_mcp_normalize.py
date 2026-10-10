"""normalize() against real recorded server payloads (discovery/raw)."""

from app.mcp.client import MALFORMED, TOOL_ERROR, ToolResult, normalize


def test_success_parses_json(raw):
    r = normalize(raw("recommend__amazon_15k")["raw_result"])
    assert r.ok and r.error_kind is None
    assert r.data["recommendations"][0]["rank"] == 1
    assert r.raw_text  # verbatim text kept for the trace


def test_schema_validation_error_is_tool_error(raw):
    r = normalize(raw("edge__string_spend")["raw_result"])
    assert not r.ok and r.error_kind == TOOL_ERROR
    assert "-32602" in r.error_msg


def test_not_found_without_iserror_is_tool_error(raw):
    # verified quirk: {"error": "Card not found: ..."} arrives with isError=false
    rec = raw("edge__details_bad_alias")["raw_result"]
    assert rec["isError"] is False
    r = normalize(rec)
    assert not r.ok and r.error_kind == TOOL_ERROR
    assert r.error_msg.startswith("Card not found")


def test_zero_results_is_still_data(raw):
    # invalid pincode returns 0 cards with no error; that's data, flagged elsewhere (not a fix)
    r = normalize(raw("followup__elig_invalid_pincode")["raw_result"])
    assert r.ok and r.data["eligible_cards_count"] == 0


def test_non_json_text_is_malformed():
    r = normalize({"content": [{"type": "text", "text": "<html>502</html>"}], "isError": False})
    assert not r.ok and r.error_kind == MALFORMED
    assert r.raw_text == "<html>502</html>"


def test_empty_content_is_malformed():
    assert normalize({"content": [], "isError": False}).error_kind == MALFORMED


def test_dict_with_error_plus_data_is_not_an_error():
    r = normalize({"content": [{"type": "text", "text": '{"error": null, "cards": []}'}]})
    assert r.ok


def test_for_model_shapes():
    assert ToolResult(ok=True, data={"a": 1}).for_model() == '{"a":1}'
    err = ToolResult(ok=False, error_kind=TOOL_ERROR, error_msg="Card not found: x").for_model()
    assert '"tool_error"' in err and "Card not found" in err
