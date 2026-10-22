# Validation record

Automated checks execute production functions extracted from the single-file mod, not simplified copies. The test runner rejects duplicate settings keys, verifies default dropdown selections and settings bindings, and validates slider ranges. It reads both the legacy YAML and the new forward-compatible annotations.

Current automated results:

- Production algorithms: 23 deterministic scenarios and 10,000 randomized geometry checks passed.
- Settings: 157 bound settings and 44 slider declarations passed validation.
- x64: full Windows DLL compilation and linking passed using LLVM-MinGW 20251104, Windows SDK C++/WinRT 10.0.26100 and Windhawk 1.7.3 import libraries.
- ARM64: full Windows DLL compilation and linking passed using the same pinned toolchain.
- Interactive Windows checks and power measurements: not executed in this Linux container.

Before using this revision as a daily driver, verify the following in Windows 11 with Windhawk:

| Area | Exercise | Expected |
| --- | --- | --- |
| Install | Replace source; enable full mode and all desired visibility switches | Cover, track info, controls and lyrics coexist |
| Preview | Enable preview with no media app; enable debug borders | Cover placeholder and each enabled section are visible; disabled playback remains disabled |
| Settings | Move slider / edit adjacent number, save | Both represent the same value; module reloads and applies it |
| Legacy settings | Open in Windhawk 1.7.3 | Numeric controls appear; new annotations do not break parsing |
| Playback | Previous / play / pause / next | Selected session responds; play icon follows reported state |
| Capabilities | App without shuffle, repeat or seeking | Unsupported controls disable or hide as configured |
| Seek | Use ±5 s after playing for a minute | Seek relative to live playback, bounded by track start/end |
| Artwork | Consecutive songs sharing an album cover | Cover remains visible; changing album replaces it |
| Session switching | Two apps, automatic and manual switching; close current app | Metadata, capabilities and lyric cues follow selected app |
| Missing lyrics | Play a track without LRCLIB cues | Lyrics blank; cover and controls continue working |
| Lyric seek/rate | Seek back/forward; change playback speed in the media app | Cue selection follows the exposed timeline |
| Component layout | Toggle each section; independent left/right cover/controls, mirror and lyric side | No shared-column overlaps |
| Tray templates | Test all configured tray anchors on Grid and StackPanel taskbars | Insert beside requested native control; unavailable anchor uses logged fallback |
| Taskbar positions | Edges, center, both sides of Start/Search/Task View/Widgets | Free slot on requested side; no taskbar button obstruction |
| Crowding | Open apps until overlay has no room; close them | Lyrics shrink or full player hides, then returns |
| Anchor removal | Hide Search/Task View/Widgets | Missing at startup falls back; an active overlay hides if its anchor disappears |
| Monitors / DPI | Select each attached monitor; change scale; disconnect selected display | Re-evaluate placement; inspect logs for unsupported template or monitor changes |
| Hiding | Fullscreen, paused idle timeout, no session | Hide according to settings; return without lost size constraints |
| Power | Compare plugged-in versus battery/energy saver with visualizer and scrolling enabled | Optional capture/marquee stops on battery; lyrics still advance |
| Reload / unload | Save settings while a lookup is running; disable; restart Explorer | No leftover player column, frozen Explorer or worker executing after unload |

Use Task Manager / Windows Performance Recorder to measure idle and playback CPU and wakeups, then compare against the original with identical settings. No numeric CPU, memory, energy or battery claim is supported yet.
