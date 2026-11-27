import json
import math
import os
from pathlib import Path
import re
import tempfile


def config_path():
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'world-compute-cell/cameras.json'


def validate_camera(name, entry):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        raise ValueError('Use a camera name starting with a letter, with only letters, numbers, and underscores.')
    if not isinstance(entry['device'], str) or not Path(entry['device']).is_absolute():
        raise ValueError('Camera device must be an absolute path.')
    fps = entry['fps']
    if isinstance(fps, bool) or not isinstance(fps, (int,float)) or not math.isfinite(fps) or not 0 < fps <= 120:
        raise ValueError('Frame rate must be between 0 and 120.')
    if not isinstance(entry['model'], str) or not isinstance(entry['bus'], str):
        raise ValueError('Invalid camera identity.')


def load(path=None):
    path = path or config_path()
    if not path.exists():
        return {'version': 1, 'cameras': {}}
    try:
        data = json.loads(path.read_text())
        if data['version'] != 1 or not isinstance(data['cameras'], dict):
            raise ValueError('Unsupported camera configuration.')
        for name, entry in data['cameras'].items():
            validate_camera(name, entry)
        return data
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f'Cannot read camera configuration at {path}: {error}') from None


def save(data, path=None):
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(data, handle, indent=2)
        handle.write('\n')
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def add(data, name, camera, fps):
    entry = {'device': camera.device, 'model': camera.name, 'bus': camera.bus, 'fps': fps}
    validate_camera(name, entry)
    if name in data['cameras']:
        raise ValueError(f'{name} is already configured. Remove it first with: cell cameras remove {name}')
    for existing in data['cameras'].values():
        if Path(existing['device']).resolve() == Path(camera.device).resolve():
            raise ValueError('This device is already configured under another name.')
    data['cameras'][name] = entry
