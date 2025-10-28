from triage.utils import clean_string, validate_file_name

def test_clean_string():
    assert clean_string("  Hello World  ") == "hello_world"
    assert clean_string("  HeLlO_WoRlD!!  ") == "hello_world"
    assert clean_string("!@#$%^&*()") == ""
    assert clean_string("  a b  c   d ") == "a_b_c_d"

def test_validate_file_name():
    assert validate_file_name("title-issuer-recipient-2023_01_01.pdf") == True
    assert validate_file_name("a_b-c_d-e_f-2023_01_01.txt") == True
    assert validate_file_name("123-456-789-2023_01_01") == True
    assert validate_file_name("title-issuer-recipient-2023_01_01") == True
    assert validate_file_name("title-issuer-recipient-2023_1_1.pdf") == False
    assert validate_file_name("title-issuer-recipient-2023_01.pdf") == False
    assert validate_file_name("title-issuer-recipient.pdf") == False
    assert validate_file_name("title-issuer-2023_01_01.pdf") == False
    assert validate_file_name("title--recipient-2023_01_01.pdf") == False
