static void TestDoubleClick() {
    using State = DoubleClickGesture::State;
    using Result = State::Result;
    State state;
    assert(state.Click(0, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Flush()); // One isolated click executes one delayed single action.
    assert(!state.Flush());
    assert(state.Click(1000, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Click(1200, 11, 9, 500, 2, 2) == Result::Double);
    assert(!state.Flush()); // No extra play/pause after a double-click.
    assert(state.Click(1300, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Flush()); // Triple-click is one double and one single.
    assert(state.Click(2000, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Click(2501, 10, 10, 500, 2, 2) == Result::FlushSingle);
    assert(state.Flush()); // Two slow clicks retain both single actions.
    assert(state.Click(3000, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Click(3100, 13, 10, 500, 2, 2) == Result::FlushSingle);
    assert(state.Click(3200, 13, 13, 500, 2, 2) == Result::FlushSingle);
    assert(state.Flush()); // Fast but distant clicks must not become doubles.
    assert(state.Click(4000, 10, 10, 500, 2, 2) == Result::Pending);
    assert(state.Click(4500, 12, 12, 500, 2, 2) == Result::Double);
    assert(!state.Flush()); // Windows interval and distance boundaries are inclusive.
    int doubles = 0, singles = 0;
    for (unsigned i = 0; i < 1000; ++i) {
        auto result = state.Click(10000 + i*100, 0, 0, 500, 2, 2);
        doubles += result == Result::Double;
        singles += result == Result::FlushSingle;
    }
    singles += state.Flush();
    assert(doubles == 500 && singles == 0);
    std::cout << "PASS: single/double/triple clicks, interval/distance boundaries and 1,000 rapid clicks\n";
}
