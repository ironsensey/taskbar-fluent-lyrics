#!/usr/bin/env python3
"""Install pinned cross-compilation tools outside the checkout (Linux x64)."""
from pathlib import Path
import argparse
import hashlib
import platform
import subprocess
import tarfile
import urllib.request
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path('/workspace/.taskbar-player-toolchain'))
args = parser.parse_args()
if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
    parser.error('This optional cross-compiler bootstrap requires Linux x64. On Windows, compile the source in Windhawk.')
root = args.root.resolve()
root.mkdir(parents=True, exist_ok=True)
cache = root / 'downloads'
cache.mkdir(exist_ok=True)

def download(name, url, expected):
    path = cache / name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        temporary = path.with_suffix(path.suffix + '.part')
        print('Downloading', name, flush=True)
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
            temporary.unlink()
            raise RuntimeError(f'Checksum mismatch: {name}')
        temporary.replace(path)
    print('Verified', name, flush=True)
    return path

llvm = download('llvm-mingw.tar.xz',
    'https://github.com/mstorsjo/llvm-mingw/releases/download/20251104/llvm-mingw-20251104-ucrt-ubuntu-22.04-x86_64.tar.xz',
    '3aed6fa47be909884cb3e5634d6b7254604d7104832d6312f8435fb23d5a9bab')
if not (root / 'llvm-mingw-20251104-ucrt-ubuntu-22.04-x86_64/bin/clang++').exists():
    with tarfile.open(llvm) as archive:
        archive.extractall(root, filter='data')
sevenzip = download('7zip.deb',
    'https://deb.debian.org/debian/pool/main/7/7zip/7zip_25.01+dfsg-1~deb13u2_amd64.deb',
    'b2cb210bee3be6a10230b38b8645d71846d19364b157f44fd08e1a54cae1652f')
sevenzip_root = root / '7zip'
if not (sevenzip_root / 'usr/lib/7zip/7z').exists():
    subprocess.run(['dpkg-deb', '-x', str(sevenzip), str(sevenzip_root)], check=True)
installer = download('windhawk_setup.exe',
    'https://github.com/ramensoftware/windhawk/releases/download/v1.7.3/windhawk_setup.exe',
    '5116cc1703384aac88b8d7a3b57f172aea5da32b6df7355fb2f8247d23813c8f')
windhawk = root / 'windhawk'
if not (windhawk / 'Compiler/include/windhawk_api.h').exists():
    subprocess.run([str(sevenzip_root / 'usr/lib/7zip/7z'), 'x', str(installer), f'-o{windhawk}', '-y'], check=True, stdout=subprocess.DEVNULL)
sdk = download('windows-sdk.nupkg',
    'https://api.nuget.org/v3-flatcontainer/microsoft.windows.sdk.cpp/10.0.26100.3916/microsoft.windows.sdk.cpp.10.0.26100.3916.nupkg',
    '21dfb5db3397425ee428e0fd54cedc51af52ddd10c82433a7cdb483ecbb284ad')
projection = root / 'sdk/cppwinrt'
numerics = root / 'sdk/numerics'
projection.mkdir(parents=True, exist_ok=True)
numerics.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(sdk) as archive:
    prefix = 'c/Include/10.0.26100.0/cppwinrt/'
    for item in archive.infolist():
        if item.is_dir():
            continue
        if item.filename.startswith(prefix):
            relative = Path(item.filename[len(prefix):])
            if relative.is_absolute() or '..' in relative.parts:
                raise RuntimeError('Unexpected SDK archive path')
            destination = projection / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(item))
        elif item.filename.rsplit('/', 1)[-1].startswith(('WindowsNumerics', 'DirectXMath')):
            (numerics / item.filename.rsplit('/', 1)[-1]).write_bytes(archive.read(item))
print('Cross-compiler ready:', root)
