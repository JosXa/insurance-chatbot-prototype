import pytest

from core.dialogstates import DialogStates

INITIAL_STATE = "test0"


@pytest.fixture
def ds():
    return DialogStates(INITIAL_STATE)


def test_basic_usage(ds: DialogStates):
    def states():
        return list(ds.iter_states())

    assert states() == [INITIAL_STATE]

    ds.put("test1")
    assert states() == ["test1"]
    assert states() == ["test1"]

    ds.put(("test2A", "test2B"))
    ds.update_step()
    assert states() == [("test2A", "test2B")]

    with pytest.raises(ValueError):
        ds.put(("1", "2", "3", -1))  # negative lifetime


def test_lifetime(ds: DialogStates):
    def states():
        return list(ds.iter_states())

    ds.put(("test0", 1))
    assert states() == ["test0", INITIAL_STATE]
    ds.update_step()
    assert states() == ["test0", INITIAL_STATE]
    ds.update_step()
    assert states() == [INITIAL_STATE]

    ds.put(("test1", 2))
    for _ in range(3):
        assert states() == ["test1", INITIAL_STATE]
        ds.update_step()
    assert states() == [INITIAL_STATE]

    ds.put((("test1A", "test1B"), 4))
    assert states() == [("test1A", "test1B"), INITIAL_STATE]
    ds.update_step()
    ds.put(("test2", 2))
    for _ in range(3):
        assert states() == ["test2", ("test1A", "test1B"), INITIAL_STATE]
        ds.update_step()
    assert states() == [("test1A", "test1B"), INITIAL_STATE]
    ds.update_step()
    assert states() == [INITIAL_STATE]
