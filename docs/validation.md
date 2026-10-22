# Validation record

Automated checks execute production functions extracted from the single-file mod, not simplified copies. The C++ UI-dispatch guard is also tested for success, a generic exception and a simulated C++/WinRT HRESULT error; this verifies exception containment, not live Windows hook behavior. The test runner rejects duplicate settings keys, verifies default dropdown selections and settings bindings, and validates slider ranges. It reads both the legacy YAML and the new forward-compatible annotations.

The screenshot shows **explorer.exe – System Error, Exception Processing Message 0xc0000005**, and the user reports it on every settings change, also disrupting TranslucentTB. This is a native access violation, not a C++ exception that ordinary `catch` blocks can reliably catch. The former callback explicitly requested DLL unload/reload on settings saves. That policy has been removed in 3.0.3; callbacks now request no reload, and producer/worker quiescence precedes mutation of settings and UI reconstruction. Same-taskbar edits reuse the existing XAML root. The causal link to the user's exact native crash remains unconfirmed without a Windows reproduction or dump.

The default remains the taskbar left edge. Upgrades preserve existing saved positions; select the left-edge option once if required. Before testing this revision, restart Explorer once after replacing the disabled old mod to clear callbacks from the prior DLL. Live Explorer/TranslucentTB behavior is not executed in this Linux environment.

Current automated results:

- Version 3.0.4 metadata: accepted by the official Windhawk mod parser. `x86-64` is a single valid value covering x64 and ARM64; it must not be followed by `arm64` on the same line.
- Single-file structure: no project-local includes; only the `.wh.cpp` is needed for installation.

- Compact preset: tested default 316-DIP budget, smaller custom sizes, unlimited/oversized saved sizes, valid constraints, icon fit, opt-out and unchanged lyrics-only sizing. Geometry confirms a 316-DIP player fits a free slot that rejects the previous 500-DIP layout.
- Production algorithms: 26 deterministic scenarios and 10,000 randomized geometry checks passed.
- Production settings callback: 1,000 saves with both successful and rejected updates requested no DLL reload. The former forced-reload callback is rejected by the mutation test.
- Production settings lifecycle: normal application and pause/stop/drain/reconfigure/resume failures were exercised; producer recovery was checked.
- Production worker admission: 100 cycles with active readers blocked new jobs during settings changes and drained old jobs before mutating configuration. Captured-resource destruction was checked before a job is counted as drained.
- AddressSanitizer / UndefinedBehaviorSanitizer: regression harness passed; this does not instrument Explorer or Windows XAML.
- Settings: 158 bound settings and 44 slider declarations passed validation.
- x64: full Windows DLL compilation and linking passed using LLVM-MinGW 20251104, Windows SDK C++/WinRT 10.0.26100 and Windhawk 1.7.3 import libraries.
- ARM64: full Windows DLL compilation and linking passed using the same pinned toolchain.
- Interactive Windows checks and power measurements: not executed in this Linux container.

Before using this revision as a daily driver, verify the following in Windows 11 with Windhawk:

| Area | Exercise | Expected |
| --- | --- | --- |
| Install | Replace source; enable full mode and all desired visibility switches | Cover, track info, controls and lyrics coexist |
| Compact layout | Leave compact mode on; test long titles, cover, lyrics and three buttons | Content fits about 316 DIPs; names truncate; controls remain usable |
| Preview | Enable preview with no media app; enable debug borders | Cover placeholder and each enabled section are visible; disabled playback remains disabled |
| Settings | Move slider / edit adjacent number, save | Both represent the same value; UI rebuilds in place, without DLL unload |
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
| TranslucentTB | Enable the mod alongside TranslucentTB, change placement, restart Explorer | Explorer stays running and both apps recover their taskbar state; not yet verified |
| Reload / unload | Save settings while a lookup is running; disable; restart Explorer | No leftover player column, frozen Explorer or worker executing after unload |

Use Task Manager / Windows Performance Recorder to measure idle and playback CPU and wakeups, then compare against the original with identical settings. No numeric CPU, memory, energy or battery claim is supported yet.
