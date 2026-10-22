#!/usr/bin/env python3
"""Build Windows DLLs for compile validation; install the .wh.cpp through Windhawk."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--toolchain', type=Path, default=Path(os.environ.get('TASKBAR_PLAYER_TOOLCHAIN', '/workspace/.taskbar-player-toolchain')))
parser.add_argument('--arch', action='append', choices=('x86_64', 'aarch64'), help='Repeat to compile both; defaults to x86_64.')
args = parser.parse_args()
root = args.toolchain.resolve()
sdk = root / 'sdk/cppwinrt'
source = repo / 'taskbar-fluent-lyrics.wh.cpp'
text = source.read_text(encoding='utf-8')
version = re.search(r'^// @version\s+(\S+)', text, re.M)[1]
mod_id = re.search(r'^// @id\s+(\S+)', text, re.M)[1]
extra = re.search(r'^// @compilerOptions\s+(.+)', text, re.M)[1].split()
output = repo / 'build'
output.mkdir(exist_ok=True)

# Windows include lookup is case-insensitive; the official SDK uses lowercase files.
def directory_tree(path, top=False):
    return {'type': 'directory', 'name': str(path) if top else path.name,
            'contents': [directory_tree(child) if child.is_dir() else
                         {'type': 'file', 'name': child.name, 'external-contents': str(child)}
                         for child in sorted(path.iterdir())]}

if not sdk.exists():
    parser.error('Run python3 tools/bootstrap.py first.')
overlay = root / 'case-insensitive-sdk.json'
overlay.write_text(json.dumps({'version': 0, 'case-sensitive': False, 'roots': [directory_tree(sdk, True)]}))
for architecture in args.arch or ['x86_64']:
    llvm = root / 'llvm-mingw-20251104-ucrt-ubuntu-22.04-x86_64'
    compiler = llvm / f'bin/{architecture}-w64-mingw32-clang++'
    engine = root / 'windhawk/Engine/$R1' / ('64' if architecture == 'x86_64' else 'arm64') / 'windhawk.lib'
    destination = output / f'taskbar-fluent-lyrics-{architecture}.dll'
    command = [str(compiler), '-std=c++23', '-O2', '-shared', '-s', '-fms-extensions',
               '-DUNICODE', '-D_UNICODE', '-DWINVER=0x0A00', '-D_WIN32_WINNT=0x0A00',
               '-D_WIN32_IE=0x0A00', '-DNTDDI_VERSION=0x0A000008', '-D__USE_MINGW_ANSI_STDIO=0',
               '-DWH_MOD', f'-DWH_MOD_ID=L"{mod_id}"', f'-DWH_MOD_VERSION=L"{version}"',
               '-DDIRECTXMATH_H', '-D_ARM64_BARRIER_ISH=0xB', '-include', 'DirectXMath.h',
               '-include', 'windhawk_api.h', '-I' + str(root / 'windhawk/Compiler/include'),
               '-isystem', str(root / 'sdk/numerics'), '-isystem', str(sdk),
               '-ivfsoverlay', str(overlay), '-Wno-pragma-pack', '-Wno-pragma-system-header-outside-header',
               '-Wno-nonportable-include-path', str(source), str(engine), *extra,
               '-Wl,--export-all-symbols', '-o', str(destination)]
    subprocess.run(command, cwd=repo, check=True)
    print('PASS:', architecture, destination.name, flush=True)
