from engine.core.clock import Clock


def test_initial_tick_is_zero():
    assert Clock().tick == 0


def test_advance_increments_by_one():
    clock = Clock()
    clock.advance()
    assert clock.tick == 1


def test_multiple_advances_accumulate():
    clock = Clock()
    for _ in range(5):
        clock.advance()
    assert clock.tick == 5
