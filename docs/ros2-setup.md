# First ROS 2 setup

The first enabled implementation scope is ROS 2 installation and communication
verification. Cell runtime packages and physical robot integration remain future work.

## Environment

Use Ubuntu 24.04 with ROS 2 Jazzy. The initial workstation uses x86_64 Ubuntu
24.04.4 under WSL 2. Its NVIDIA RTX 3060 is visible from Linux; these communication
demos do not use the GPU. This is a development baseline, not validation of WSL
for physical control, camera transport, or real-time requirements.

## Install

Start with the [official Jazzy installation instructions](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).
Ensure a UTF-8 locale and Ubuntu Universe are enabled. Configure the official
`ros2-apt-source` package as described there. The first workstation used source
package version 1.3.0. Then install:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  ros-jazzy-ros-base ros-jazzy-demo-nodes-cpp ros-jazzy-demo-nodes-py
```

Review the package plan before applying it to an existing station. The initial
installation added 301 packages and upgraded the SQLite system library; it did
not perform a full system upgrade. No shell startup file needs changing.

## Verify

From a checkout inside Ubuntu:

```bash
bash scripts/check-ros2.sh
```

The script runs an upstream C++ talker and Python listener, verifies a message with
`ros2 topic echo`, and cleans up the demo processes. All commands are bounded by
timeouts. It uses domain 87 and localhost discovery, with Fast DDS explicitly
selected. Reserve that domain for this check. Domain IDs separate ROS graphs;
they are not an authentication mechanism.

For interactive use, set these in each Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=87
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset ROS_STATIC_PEERS
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Run `ros2 run demo_nodes_cpp talker` in one terminal and
`ros2 run demo_nodes_py listener` in another. Stop both with Ctrl-C.

## Access and scope

On Windows, enter the existing distribution using:

```powershell
wsl.exe -d WorldCompute-Ubuntu -u robot
```

Remote SSH addresses, credentials, and key material belong in private operator
configuration, not this repository. Run demos as the ordinary Linux user;
installation requires administrator/root access.

This check establishes local ROS communication only. It does not connect a robot,
stream cameras, validate inter-machine discovery, or start a cell service.

## Verified on 26 November 2026

The workstation passed the scripted check: the C++ publisher emitted
`Hello World: 1`, the Python listener received it, and the CLI echo returned the
same payload. Demo processes exited after the check. The eight existing World
Compute services were still running afterward. This was a communication test;
robot movement and camera capture were not exercised.
