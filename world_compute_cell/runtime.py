"""Internal ROS setup/launch mechanics; the user-facing CLI stays camera-oriented."""
import hashlib
import shutil
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import urllib.request

BUNDLED_SOURCE = Path(__file__).parent / 'ros_packages/world_compute_camera'
ROS_SETUP = Path('/opt/ros/jazzy/setup.bash')


def bundled_files():
    return sorted(p for p in BUNDLED_SOURCE.rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')


def workspace_path():
    # An upgraded wheel gets a separate runtime; existing processes keep their files.
    digest = hashlib.sha256()
    for path in bundled_files():
        digest.update(str(path.relative_to(BUNDLED_SOURCE)).encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
    if not bundled_files():
        raise ValueError('Bundled camera runtime is missing. Reinstall world-compute-cell.')
    data_home = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return data_home / 'world-compute-cell/runtimes' / digest.hexdigest()[:16]


def prepare_workspace():
    workspace = workspace_path()
    destination = workspace / 'src/world_compute_camera'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BUNDLED_SOURCE, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    return workspace


def require_linux():
    if sys.platform != 'linux':
        raise ValueError('Run world-compute cell on your Ubuntu 24.04 camera computer. Native macOS/Windows capture is not supported yet.')


def ros_environment():
    env = os.environ.copy()
    env.update(ROS_DOMAIN_ID='87', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST', RMW_IMPLEMENTATION='rmw_fastrtps_cpp')
    for key in ('ROS_STATIC_PEERS', 'VIRTUAL_ENV', 'PYTHONHOME', 'PYTHONPATH'):
        env.pop(key, None)
    # ROS Jazzy's apt packages use Ubuntu's system Python, independently of pipx.
    env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin:' + env.get('PATH', '')
    return env


def run_ros(arguments, overlay=True, **kwargs):
    if not ROS_SETUP.exists():
        raise ValueError('The camera runtime is not installed. Run: world-compute cell setup')
    paths = [ROS_SETUP]
    if overlay:
        setup = workspace_path() / 'install/setup.bash'
        if not setup.exists():
            raise ValueError('The camera runtime is not built. Run: world-compute cell setup')
        paths.append(setup)
    command = ' && '.join('source ' + shlex.quote(str(p)) for p in paths)
    command += ' && exec ' + shlex.join(arguments)
    return subprocess.Popen(['bash', '-c', command], cwd=workspace_path(), env=ros_environment(), **kwargs)


def wait_foreground(process):
    try:
        return process.wait()
    except KeyboardInterrupt:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        return 130


def setup_runtime():
    require_linux()
    release = dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID','').strip('"') != 'ubuntu' or release.get('VERSION_ID','').strip('"') != '24.04':
        raise ValueError('Automatic setup currently supports Ubuntu 24.04 only.')
    sudo = [] if os.geteuid() == 0 else ['sudo']
    def run(args):
        subprocess.run(sudo + args, check=True)
    print('Installing camera runtime dependencies. Ubuntu may ask for your administrator password.', flush=True)
    run(['apt-get','update'])
    run(['apt-get','install','-y','--no-install-recommends','software-properties-common','ca-certificates'])
    run(['add-apt-repository','-y','universe'])
    source_installed = subprocess.run(['dpkg-query','-W','-f=${Status}','ros2-apt-source'],capture_output=True,text=True)
    if source_installed.returncode != 0 or 'install ok installed' not in source_installed.stdout:
        # Official ROS repository setup package, pinned for repeatable bootstrap.
        url = 'https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros2-apt-source_1.3.0.noble_all.deb'
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'ros2-apt-source.deb'
            with urllib.request.urlopen(url, timeout=30) as response:
                package.write_bytes(response.read())
            run(['dpkg','-i',str(package)])
    run(['apt-get','update'])
    run(['apt-get','install','-y','--no-install-recommends','ros-jazzy-ros-base',
         'python3-opencv','python3-colcon-common-extensions','v4l-utils'])
    build_runtime()
    print('Ready. Connect a camera, then run: world-compute cell cameras setup')


def build_runtime():
    prepare_workspace()
    print('Building the camera runtime…', flush=True)
    process = run_ros(['colcon', 'build', '--base-paths', 'src', '--packages-select',
                       'world_compute_camera', '--symlink-install'], overlay=False)
    if process.wait() != 0:
        raise ValueError('Camera runtime build failed. See the build output above.')
