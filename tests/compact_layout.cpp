// Execute the production compact preset against representative persisted sizes.
struct CompactTestSettings {
    bool compactLayout = true, lyricsOnly = false;
    int playerMinWidth = 600, playerMaxWidth = 600;
    int albumArtMinWidth = 32, albumArtMaxWidth = 64;
    int albumArtMinHeight = 32, albumArtMaxHeight = 32;
    int textAreaMinWidth = 0, textAreaMaxWidth = 120;
    int lyricsWidth = 230, buttonSize = 28, buttonIconSize = 16, buttonSpacing = 0;
    int playerMarginLeft = 4, playerMarginRight = 4;
    int albumArtLeftMargin = 0, albumArtRightMargin = 0;
    int textAreaLeftMargin = 5, textAreaRightMargin = 5;
    int mediaButtonsLeftMargin = 2, mediaButtonsRightMargin = 2;
};
static void TestCompactLayout() {
    CompactTestSettings s;
    ApplyCompactLayout(s);
    assert(s.playerMinWidth == 0 && s.playerMaxWidth == 0);
    assert(s.albumArtMinWidth == 28 && s.albumArtMaxWidth == 28);
    assert(s.albumArtMinHeight == 28 && s.albumArtMaxHeight == 28);
    assert(s.textAreaMaxWidth == 80 && s.lyricsWidth == 120 && s.buttonSize == 24);
    // Default panel: cover + text/margins + three buttons/margins + lyrics/gaps + insets.
    const int width = s.albumArtMaxWidth + s.textAreaMaxWidth + s.textAreaLeftMargin +
        s.textAreaRightMargin + 3*s.buttonSize + s.mediaButtonsLeftMargin +
        s.mediaButtonsRightMargin + s.lyricsWidth + 4 + 4;
    assert(width == 316);
    const auto place = PlayerGeometry::Place(1000, width, width, 2, 2, 4,
        PlayerGeometry::Anchor::LeftEdge, 0, 0, 0, {{350, 650}, {850, 1000}});
    assert(place.visible && place.x + place.width <= 346);
    const auto wide = PlayerGeometry::Place(1000, 500, 500, 2, 2, 4,
        PlayerGeometry::Anchor::LeftEdge, 0, 0, 0, {{350, 650}, {850, 1000}});
    assert(!wide.visible);
    s.textAreaMinWidth = 700; s.textAreaMaxWidth = 0;
    s.albumArtMinWidth = 200; s.albumArtMaxWidth = 0;
    s.buttonSize = 16; s.buttonIconSize = 40; s.buttonSpacing = -10;
    s.playerMarginLeft = -20; s.textAreaRightMargin = 100;
    ApplyCompactLayout(s);
    assert(s.textAreaMinWidth == 80 && s.textAreaMaxWidth == 80);
    assert(s.albumArtMinWidth == 28 && s.albumArtMaxWidth == 28);
    assert(s.buttonSize == 16 && s.buttonIconSize == 12 && s.buttonSpacing == 0);
    assert(s.playerMarginLeft == 0 && s.textAreaRightMargin == 2);
    s.lyricsWidth = 90; s.textAreaMaxWidth = 40;
    ApplyCompactLayout(s);
    assert(s.lyricsWidth == 90 && s.textAreaMaxWidth == 40 && s.textAreaMinWidth == 40);
    CompactTestSettings custom;
    custom.compactLayout = false;
    ApplyCompactLayout(custom);
    assert(custom.playerMinWidth == 600 && custom.textAreaMaxWidth == 120 && custom.lyricsWidth == 230);
    custom.compactLayout = true; custom.lyricsOnly = true;
    ApplyCompactLayout(custom);
    assert(custom.playerMinWidth == 600 && custom.lyricsWidth == 230);
    std::cout << "PASS: compact sizing, saved/unlimited constraints, custom opt-out and taskbar fit\n";
}
