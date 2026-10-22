#!/usr/bin/env python3
"""Run the production pure-C++ algorithms; validate Windhawk settings bindings."""
from pathlib import Path
import os
import argparse
import shlex
import re
import subprocess
import tempfile
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--sanitize', action='store_true', help='Run with address/undefined-behavior sanitizers')
parser.add_argument('--mutation-check', action='store_true', help='Verify regression tests reject the former forced-reload callback')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'taskbar-fluent-lyrics.wh.cpp').read_text(encoding='utf-8')

# Windhawk accepts one architecture token per metadata line, not a space-separated list.
metadata = source.split('// ==WindhawkMod==', 1)[1].split('// ==/WindhawkMod==', 1)[0]
architectures = re.findall(r'^// @architecture\s+(.+)$', metadata, re.M)
assert architectures, 'Declare the supported architectures explicitly'
assert all(value in {'x86', 'x86-64', 'amd64', 'arm64'} for value in architectures), architectures
# The installed mod must remain a single file, with no project-local includes.
assert not re.search(r'^\s*#include\s*"', source, re.M), 'Local includes would require extra mod files'
print('PASS: Windhawk architecture metadata and single-file mod structure')

def between(start, end):
    return source.split(start, 1)[1].split(end, 1)[0]

# Duplicate keys silently hide controls in ordinary YAML loaders; reject them.
class UniqueLoader(yaml.SafeLoader):
    pass

def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise AssertionError(f'Duplicate settings key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
settings_text = between('// ==WindhawkModSettings==\n/*', '*/')
settings = yaml.load(re.sub(r'(?m)^(\s*)#! ', r'\1', settings_text), Loader=UniqueLoader)
# Windhawk 1.7.3 ignores forward-compatible annotations, but must parse the same settings.
legacy_settings = yaml.load(settings_text, Loader=UniqueLoader)
assert len(legacy_settings) == len(settings)
player_settings = next(section['MainSettings'] for section in settings if 'MainSettings' in section)
player_settings = next(group['PlayerSetting'] for group in player_settings if 'PlayerSetting' in group)
assert next(item['position'] for item in player_settings if 'position' in item) == 'taskbar_left_edge'
assert 'std::wstring position             = L"taskbar_left_edge";' in source
assert 'Str(L"MainSettings.PlayerSetting.position",    L"taskbar_left_edge")' in source
assert next(item['compactLayout'] for item in player_settings if 'compactLayout' in item) is True
assert 'ApplyCompactLayout(g_settings);' in source
print('PASS: compact mode enabled by default; default position is the left edge')
bindings = set()
sliders = []

def walk(items, prefix=''):
    for item in items:
        names = [key for key in item if not key.startswith('$')]
        assert len(names) == 1, item
        name = names[0]
        value = item[name]
        path = prefix + name
        if isinstance(value, list) and value and isinstance(value[0], dict):
            # Settings groups vs configurable arrays of records.
            if isinstance(value[0], list):
                continue
            walk(value, path + '.')
        else:
            bindings.add(path)
        if item.get('$format') == 'slider':
            assert type(value) is int, path
            assert item['$min'] < item['$max'], path
            assert item['$min'] <= value <= item['$max'], path
            sliders.append(path)
        if '$options' in item and not isinstance(value, list):
            assert value in {k for option in item['$options'] for k in option}, path

walk(settings)
for key in re.findall(r'(?:Int|Str|StrAllowEmpty|Wh_GetIntSetting|Wh_GetStringSetting)\(L"([^"%]+)"', source):
    if '[' not in key:
        assert key in bindings, f'Missing settings UI for {key}'
print(f'PASS: {len(bindings)} settings bindings, {len(sliders)} sliders with bounds and number inputs')

includes = '''#include <algorithm>\n#include <cmath>\n#include <cstdint>\n#include <cwctype>\n#include <limits>\n#include <string>\n#include <unordered_map>\n#include <vector>\n'''
geometry = between('// BEGIN PORTABLE PLAYER GEOMETRY\n', '// END PORTABLE PLAYER GEOMETRY')
lyrics = source[source.index('static std::vector<LyricCue> ParseLrcLines('):source.index('static std::wstring NormalizeLyricsMatch(')]
# The chunk also includes normalization helpers, all independent of Windows APIs.
compact = between('// BEGIN PORTABLE COMPACT LAYOUT\n', '// END PORTABLE COMPACT LAYOUT')
program = includes + geometry + compact + '\nstruct LyricCue { int64_t timeMs; std::wstring text; };\n' + lyrics
# Exercise the actual dispatch guard without requiring Explorer or Windows SDK runtime.
# The stand-in supplies only the HRESULT/message interface consumed by this pure C++ guard.
program += r"""
#include <stdexcept>
namespace winrt {
struct hresult_error {
    int code() const noexcept { return -1; }
    std::wstring message() const { return L"Test HRESULT"; }
};
}
static int testLogCount = 0;
static void Wh_Log(const wchar_t*, ...) { ++testLogCount; }
using WindowThreadProc = void(*)(void*);
"""
program += source[source.index('static bool InvokeWindowThreadProc('):source.index('static bool RunFromWindowThread(')]
program += r"""
#include <atomic>
#include <chrono>
#include <mutex>
#include <thread>
#include <memory>
#include <optional>
static std::atomic<bool> g_unloading{false};
static std::atomic<bool> g_applyingSettings{false};
"""
program += between('// BEGIN PORTABLE SETTINGS LIFECYCLE\n', '// END PORTABLE SETTINGS LIFECYCLE')
program += source[source.index('static std::atomic<int> g_activeWorkerThreads'):source.index('static void WaitForThreadToExit(')]
program += r"""
using BOOL = int;
constexpr BOOL TRUE = 1, FALSE = 0;
static bool testLiveSettingsSuccess = true;
static bool ApplySettingsLive() { return testLiveSettingsSuccess; }
"""
program += source[source.index('BOOL Wh_ModSettingsChanged('):]
program += (ROOT / 'tests/settings_lifecycle.cpp').read_text()
program += (ROOT / 'tests/compact_layout.cpp').read_text()
program += (ROOT / 'tests/portable_tests.cpp').read_text()
with tempfile.TemporaryDirectory(prefix='taskbar-player-tests-') as temp:
    cpp = Path(temp, 'tests.cpp')
    binary = Path(temp, 'tests')
    cpp.write_text(program, encoding='utf-8')
    compiler = shlex.split(os.environ.get('CXX', 'g++'))
    flags = ['-std=c++20', '-O2', '-pthread', '-Wall', '-Wextra']
    if args.sanitize:
        flags += ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    subprocess.run([*compiler, *flags, str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], cwd=temp, check=True)
    if args.mutation_check:
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        mutant = program.replace('if (reload) *reload = FALSE;', 'if (reload) *reload = TRUE;', 1)
        assert mutant != program
        cpp.write_text(mutant, encoding='utf-8')
        subprocess.run([*compiler, *flags, str(cpp), '-o', str(binary)], check=True)
        rejected = subprocess.run([str(binary)], cwd=temp, capture_output=True, text=True)
        assert rejected.returncode != 0 and 'reload == FALSE' in rejected.stderr, rejected.stderr
        print('PASS: regression test rejects the former forced-DLL-reload behavior')
