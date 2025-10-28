from triage.utils import clean_string

def test_clean_string():
    assert clean_string("  Hello World  ") == "hello_world"
    assert clean_string("  HeLlO_WoRlD!!  ") == "hello_world"
    assert clean_string("!@#$%^&*()") == ""
    assert clean_string("  a b  c   d ") == "a_b_c_d"
