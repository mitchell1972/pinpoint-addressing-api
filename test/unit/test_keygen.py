from app.services.accounts import _generate_key


def test_key_has_env_prefix():
    assert _generate_key("test").startswith("pk_test_")
    assert _generate_key("live").startswith("pk_live_")


def test_key_is_long_and_unique():
    a = _generate_key("test")
    b = _generate_key("test")
    assert len(a) > 24
    assert a != b
