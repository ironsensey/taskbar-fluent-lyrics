#!/usr/bin/env python3
"""Run the production pure-C++ algorithms; validate Windhawk settings bindings."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'taskbar-fluent-lyrics.wh.cpp').read_text(encoding='utf-8')

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
program = includes + geometry + '\nstruct LyricCue { int64_t timeMs; std::wstring text; };\n' + lyrics
program += (ROOT / 'tests/portable_tests.cpp').read_text()
with tempfile.TemporaryDirectory(prefix='taskbar-player-tests-') as temp:
    cpp = Path(temp, 'tests.cpp')
    binary = Path(temp, 'tests')
    cpp.write_text(program, encoding='utf-8')
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-O2', '-Wall', '-Wextra', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
