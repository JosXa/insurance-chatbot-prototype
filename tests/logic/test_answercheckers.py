from logic.rules import answercheckers as ans


def test__parse_name():
    n = "jan Van der Linden"
    res = ans._parse_names(n)
    assert res.first_name == "Jan"
    assert res.last_name == "Van der Linden"

    n = "Van der Linden, Jan"
    res = ans._parse_names(n)
    assert res.first_name == "Jan"
    assert res.last_name == "Van der Linden"

    n = "Max Mustermann"
    res = ans._parse_names(n)
    assert res.first_name == "Max"
    assert res.last_name == "Mustermann"

    n = "Mustermann, Max"
    res = ans._parse_names(n)
    assert res.first_name == "Max"
    assert res.last_name == "Mustermann"

    assert ans._parse_names("was meinst du damit genau?") is None
