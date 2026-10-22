// Compiled with the production functions extracted by tools/test.py.
#include <cassert>
#include <iostream>
#include <random>

int main() {
    using namespace PlayerGeometry;
    auto place = [](Anchor mode, double width, double min, std::vector<Interval> items,
                    double offset = 0, double x = 400, double anchorWidth = 40) {
        return Place(1000, width, min, 4, 4, 12, mode, x, anchorWidth, offset, std::move(items));
    };
    auto p = place(Anchor::LeftEdge, 230, 72, {{400, 700}, {900, 1000}});
    assert(p.visible && p.x == 4 && p.width == 230);
    p = place(Anchor::RightEdge, 150, 150, {{400, 700}, {900, 1000}});
    assert(p.visible && p.x == 738 && p.x + p.width == 888);
    p = place(Anchor::Center, 160, 160, {{400, 700}, {900, 1000}});
    assert(p.visible && p.x + p.width <= 388); // Must not cover centered app icons.
    p = place(Anchor::LeftEdge, 230, 72, {{180, 1000}});
    assert(p.visible && p.width == 164); // Only lyrics may shrink.
    p = place(Anchor::LeftEdge, 480, 480, {{180, 1000}});
    assert(!p.visible); // Never cut off the controls to make a full player fit.
    p = place(Anchor::Before, 150, 150, {{400, 440}, {900, 1000}});
    assert(p.visible && p.x == 238);
    p = place(Anchor::After, 150, 150, {{400, 440}, {900, 1000}});
    assert(p.visible && p.x == 452);
    p = place(Anchor::LeftEdge, 230, 72, {{400, 700}, {900, 1000}}, 10000);
    assert(p.visible && p.x + p.width <= 388); // Offset cannot steal icon clicks.
    assert(!Place(0, 200, 72, 4, 4, 12, Anchor::Center, 0, 0, 0, {}).visible);
    assert(!place(Anchor::Center, 200, 200, {{0, 1000}}).visible);
    // Multiple monitors and DPI scales are independent DIP coordinate spaces.
    std::mt19937 rng(1729);
    for (int i = 0; i < 10000; ++i) {
        const double extent = 300 + rng() % 3600;
        const double desired = 40 + rng() % 800;
        const double minimum = std::min(72.0, desired);
        const double gap = rng() % 30;
        std::vector<Interval> occupied;
        for (int k = 0; k < 8; ++k) {
            double start = rng() % (int)extent;
            occupied.push_back({start, std::min(extent, start + 1 + rng() % 200)});
        }
        const auto q = Place(extent, desired, minimum, 4, 4, gap,
            static_cast<Anchor>(rng() % 5), extent / 2, 40,
            (int)(rng() % 2000) - 1000, occupied);
        if (!q.visible) continue;
        assert(std::isfinite(q.x) && std::isfinite(q.width));
        assert(q.x >= 4 - 1e-7 && q.x + q.width <= extent - 4 + 1e-7);
        assert(q.width >= minimum && q.width <= desired);
        for (auto r : occupied) {
            if (!(q.x + q.width <= r.left - gap + 1e-7 || q.x >= r.right + gap - 1e-7)) {
                std::cerr << "collision i=" << i << " extent=" << extent << " desired=" << desired << " min=" << minimum << " q=" << q.x << "," << q.width << " r=" << r.left << "," << r.right << " gap=" << gap << "\n";
                assert(false);
            }
        }
    }
    auto cues = ParseLrcLines(L"[ar:Artist]\r\n[00:02.50][00:04.00] second \r\n[00:01.001]first\n[00:03.00]\n");
    assert(cues.size() == 4 && cues[0].timeMs == 1001 && cues[1].timeMs == 2500);
    assert(cues[1].text == L"second" && cues[2].text.empty() && cues[3].timeMs == 4000);
    cues = ParseLrcLines(L"[00:01]a\n[00:01]b\n[00:01]\n");
    assert(cues.size() == 1 && cues[0].text == L"b");
    assert(ParseLrcLines(L"[ar:x]\n[00:60]bad\n[-1:10]bad\n[01:NaN]bad\n[00:inf]bad\n").empty());
    std::wstring large;
    for (int i = 0; i < 5000; ++i) large += L"[00:01]x\n";
    assert(ParseLrcLines(large).size() == 1);
    assert(LyricsRomanizeIndic(L"Hello, world! 123") == L"Hello, world! 123");
    assert(LyricsHasIndicScript(L"दिल") && LyricsHasIndicScript(L"ਪਿਆਰ"));
    auto roman = LyricsRomanizeIndic(L"Love दिल / ਪਿਆਰ 123");
    assert(!LyricsHasIndicScript(roman));
    assert(roman.find(L"Love ") == 0 && roman.find(L"123") != std::wstring::npos);
    for (const auto& english : {L"I'm STILL here — don't change Me!", L"Café, naïve, déjà vu 🎵", L"love YOU 123 & me", L"English\t  stays\nEnglish", L"👨‍👩‍👧‍👦 ❤️", L"\u200Duntouched\uFEFF"})
        assert(LyricsRomanizeIndic(english) == english);
    assert(LyricsRomanizeIndic(L"तुम मेरे दिल में हो") == L"tum mere dil mein ho");
    assert(LyricsRomanizeIndic(L"ਪਿਆਰ") == L"pyaar");
    assert(LyricsRomanizeIndic(L"I LOVE तुम, ਪਿਆਰ! Café") == L"I LOVE tum, pyaar! Café");
    assert(LyricsRomanizeIndic(L"👨‍👩‍👧‍👦 दिल ❤️") == L"👨‍👩‍👧‍👦 dil ❤️");
    assert(LyricsRomanizeIndic(L"  दिल\t\tEnglish\nਪਿਆਰ!  ") == L"  dil\t\tEnglish\npyaar!  ");
    int callbackCount = 0;
    assert(InvokeWindowThreadProc([](void* param) { ++*static_cast<int*>(param); }, &callbackCount));
    assert(callbackCount == 1);
    assert(!InvokeWindowThreadProc([](void*) { throw std::runtime_error("callback failure"); }, nullptr));
    assert(!InvokeWindowThreadProc([](void*) { throw winrt::hresult_error{}; }, nullptr));
    assert(testLogCount == 2);
    TestSettingsLifecycle();
    std::cout << "PASS: 26 scenarios and 10,000 randomized placement checks\n";
}
