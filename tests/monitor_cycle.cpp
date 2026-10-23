static void TestMonitorCycle() {
    using MonitorCycle::Next;
    assert(Next({}, 0) == -1);
    assert(Next({true}, 0) == 0);
    assert(Next({false}, 0) == -1);
    assert(Next({true, true}, 0) == 1);
    assert(Next({true, true}, 1) == 0);
    assert(Next({true, false, true}, 0) == 2);
    assert(Next({true, false, true}, 2) == 0);
    assert(Next({false, false, true}, 2) == 2);
    assert(Next({false, true, false}, 0) == 1);
    assert(Next({false, true, false}, -1) == 1);
    assert(Next({false, true, false}, 99) == 1);
    assert(Next({false, false}, -1) == -1);
    for (int count = 1; count <= 10; ++count) {
        for (int mask = 0; mask < (1 << count); ++mask) {
            std::vector<bool> available;
            for (int i = 0; i < count; ++i) available.push_back((mask & (1 << i)) != 0);
            for (int current = 0; current < count; ++current) {
                const int next = Next(available, current);
                if (!mask) { assert(next == -1); continue; }
                assert(next >= 0 && next < count && available[next]);
                if (next == current) assert(mask == (1 << current));
                else {
                    const int steps = (next - current + count) % count;
                    for (int step = 1; step < steps; ++step)
                        assert(!available[(current + step) % count]);
                }
            }
        }
    }
    std::cout << "PASS: monitor cycling, wraparound, missing taskbars and all availability sets up to 10 displays\n";
}
