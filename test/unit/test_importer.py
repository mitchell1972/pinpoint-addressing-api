from app.services.importer import parse_csv


def test_parse_csv_coerces_types():
    text = "lat,lng,landmark,confidence\n6.5,3.3,Test Spot,0.8\n"
    rows = parse_csv(text)
    assert len(rows) == 1
    assert rows[0]["lat"] == 6.5
    assert rows[0]["lng"] == 3.3
    assert rows[0]["landmark"] == "Test Spot"
    assert rows[0]["confidence"] == 0.8


def test_parse_csv_blank_optionals_become_none():
    text = "lat,lng,landmark,state\n6.5,3.3,,Lagos\n"
    rows = parse_csv(text)
    assert rows[0]["landmark"] is None  # empty cell -> None
    assert rows[0]["state"] == "Lagos"
    assert rows[0]["confidence"] is None  # column absent -> None


def test_parse_csv_multiple_rows():
    text = "lat,lng\n6.5,3.3\n6.6,3.4\n"
    assert len(parse_csv(text)) == 2
