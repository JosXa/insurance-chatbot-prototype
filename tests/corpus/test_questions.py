from corpus.questions import all_questions, get_question_by_id


def test_all_question_examples_are_valid():
    for q in (x for x in all_questions if x.example):
        result = q.match_input(q.example)
        if hasattr(result, "groups"):
            print(result.groups())
        assert bool(result), f"{q.id}'s example failed to match"


def test_phone():
    q = get_question_by_id("phone_number")
    t = "Die nummer ist die +49     172 85  32 -    3 und sie ist wundertoll"
    assert q.match_input(t) == "+49 172 85 32 - 3"

    assert not q.match_input("abc test 123 4 testtest")


def test_imei():
    q = get_question_by_id("imei")
    assert not q.match_input("test")
    assert not q.match_input("12345678901234")  # one short
