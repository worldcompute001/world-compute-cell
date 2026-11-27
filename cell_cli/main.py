import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from .cameras import discover
from .config import add, load, save
from .runtime import require_linux, run_ros, setup_runtime, wait_foreground


def list_cameras(as_json=False):
    require_linux()
    cameras = discover()
    if as_json:
        print(json.dumps([camera.to_dict() for camera in cameras], indent=2))
    elif not cameras:
        print('No Linux cameras found. Plug in a USB camera and try again.\n'
              'On WSL, Windows cameras must be exposed to Linux or connected through an adapter.')
    else:
        for i, camera in enumerate(cameras,1):
            print(f'{i}. {camera.name} — {camera.state}\n   {camera.device}')
        if any(c.state == 'permission denied' for c in cameras):
            print('Device permission denied. On Ubuntu, check membership in the video group and log in again after changes.')
    return cameras


def configure(args):
    cameras = list_cameras()
    available = [c for c in cameras if c.state == 'available']
    if not available:
        raise ValueError('No accessible capture device is available to configure.')
    if args.device:
        matches = [c for c in available if Path(c.device).resolve() == Path(args.device).resolve()]
        if len(matches) != 1:
            raise ValueError('The selected device is not an accessible capture camera.')
        camera = matches[0]
    else:
        if not sys.stdin.isatty():
            raise ValueError('For unattended setup, supply --device and --name.')
        answer = input('Choose a camera number: ').strip()
        if not answer.isdigit() or not 1 <= int(answer) <= len(cameras):
            raise ValueError('Choose a number from the camera list.')
        camera = cameras[int(answer)-1]
        if camera.state != 'available':
            raise ValueError('That device is not accessible.')
    name = args.name
    if not name:
        if not sys.stdin.isatty():
            raise ValueError('For unattended setup, supply --name.')
        name = input('Give it a name (for example desk or side): ').strip()
    data = load()
    add(data, name, camera, args.fps)
    save(data)
    print(f'Saved {name}. Start reading with: cell cameras start {name}')


def start(name):
    require_linux()
    data = load()['cameras']
    if not data:
        raise ValueError('No cameras configured. Run: cell cameras setup')
    if not name:
        if len(data) != 1:
            raise ValueError('Choose a configured camera: ' + ', '.join(data))
        name = next(iter(data))
    if name not in data:
        raise ValueError(f'Unknown camera {name}. Run: cell cameras configured')
    entry = data[name]
    cameras = discover()
    selected = next((c for c in cameras if Path(c.device).resolve() == Path(entry['device']).resolve()), None)
    if selected is None or selected.state != 'available':
        raise ValueError(f'{name} is disconnected or inaccessible. Reconnect it and run: cell cameras list')
    if selected.name != entry['model'] or (entry['bus'] and selected.bus != entry['bus']):
        raise ValueError('Device identity changed. Run camera setup again instead of using a different camera silently.')
    import fcntl
    import hashlib
    # Prevent two CLI readers from opening the same device. Other apps may still own it.
    lockdir = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache')) / 'world-compute-cell'
    lockdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(Path(selected.device).resolve()).encode()).hexdigest()
    with (lockdir / (key+'.lock')).open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('This camera already has a cell reader running.') from None
        print(f'Starting {name}. Press Ctrl-C to stop.', flush=True)
        process = run_ros(['ros2','run','world_compute_camera','camera_reader','--ros-args',
                           '-r',f'__node:={name}_camera_reader',
                           '-p',f'device:={selected.device}','-p',f'camera_name:={name}',
                           '-p',f'fps:={float(entry["fps"])}'], start_new_session=True)
        return wait_foreground(process)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='cell', description='Set up your local robotics workspace.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('setup', help='Install and build the camera runtime on Ubuntu 24.04')
    cameras = commands.add_parser('cameras', help='Find, configure, and read your cameras')
    actions = cameras.add_subparsers(dest='action', required=True)
    listing = actions.add_parser('list', help='Inspect connected capture devices')
    listing.add_argument('--json', action='store_true')
    configure_parser = actions.add_parser('setup', help='Choose and name a connected camera')
    configure_parser.add_argument('--device')
    configure_parser.add_argument('--name')
    configure_parser.add_argument('--fps', type=float, default=15.0)
    actions.add_parser('configured', help='Show saved camera choices')
    remove = actions.add_parser('remove', help='Forget a saved camera (does not stop a running reader)')
    remove.add_argument('name')
    launch = actions.add_parser('start', help='Read a saved camera until Ctrl-C')
    launch.add_argument('name', nargs='?')
    args = parser.parse_args(argv)
    try:
        if args.command == 'setup':
            setup_runtime()
        elif args.action == 'list':
            list_cameras(args.json)
        elif args.action == 'setup':
            configure(args)
        elif args.action == 'configured':
            data = load()['cameras']
            for name, entry in data.items():
                print(f'{name}: {entry["model"]} — {entry["device"]} ({entry["fps"]} fps requested)')
            if not data:
                print('No cameras configured. Run: cell cameras setup')
        elif args.action == 'remove':
            data = load()
            if args.name not in data['cameras']:
                raise ValueError(f'Unknown camera: {args.name}')
            del data['cameras'][args.name]
            save(data)
            print(f'Forgot {args.name}.')
        elif args.action == 'start':
            return start(args.name)
        return 0
    except KeyboardInterrupt:
        print('\nStopped.')
        return 130
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'cell: {error}', file=sys.stderr)
        return 1
