"""Internal ROS setup/launch mechanics; the user-facing CLI stays camera-oriented."""
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ROS_SETUP = Path('/opt/ros/jazzy/setup.bash')


def require_linux():
    if sys.platform != 'linux':
        raise ValueError('Run cell on your Ubuntu 24.04 camera computer. Native macOS/Windows capture is not supported yet.')


def ros_environment():
    env = os.environ.copy()
    env.update(ROS_DOMAIN_ID='87', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST', RMW_IMPLEMENTATION='rmw_fastrtps_cpp')
    env.pop('ROS_STATIC_PEERS', None)
    return env


def run_ros(arguments, overlay=True, **kwargs):
    if not ROS_SETUP.exists():
        raise ValueError('The camera runtime is not installed. Run: cell setup')
    paths = [ROS_SETUP]
    if overlay:
        setup = ROOT / 'install/setup.bash'
        if not setup.exists():
            raise ValueError('The camera runtime is not built. Run: cell setup')
        paths.append(setup)
    command = ' && '.join('source ' + shlex.quote(str(p)) for p in paths)
    command += ' && exec ' + shlex.join(arguments)
    return subprocess.Popen(['bash', '-c', command], cwd=ROOT, env=ros_environment(), **kwargs)


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
    print('Building the camera runtime…', flush=True)
    process = run_ros(['colcon','build','--packages-select','world_compute_camera','--symlink-install'], overlay=False)
    if process.wait() != 0:
        raise ValueError('Camera runtime build failed. See the build output above.')
    print('Ready. Connect a camera, then run: cell cameras setup')
