# Read your first camera

You need an Ubuntu 24.04 computer with ROS 2 Jazzy and a Linux-visible USB camera.
You do not need our workstation, a robot, camera presets, or calibration.

This first node does one thing: read the device you select and publish ROS images.

## 1. Find your camera

Plug it in, then run:

```bash
sudo apt-get install v4l-utils
v4l2-ctl --list-devices
ls -l /dev/v4l/by-id/
```

Choose a video capture device from the list. A camera can expose multiple device
nodes, including metadata nodes; inspect its supported capture formats with:

```bash
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

`/dev/video0` is an example, not a preset. Prefer the corresponding
`/dev/v4l/by-id/...-video-index0` path when available, because numeric device
indices can change. If permissions prevent access, check `ls -l /dev/video0` and
`groups`. On a typical Ubuntu installation, joining the `video` group and logging
out/back in grants device access. Avoid running the node as root.

**WSL:** a Windows webcam is not automatically a Linux video device. If no video
device appears, this direct reader cannot use it. Run on a Linux camera host or
provide a capture adapter. Our [Windows station bridge](cameras.md) is one optional,
station-specific example. Do not open a camera already owned by another process.

## 2. Build

From this repository's root:

```bash
sudo apt-get install --no-install-recommends \
  python3-opencv python3-colcon-common-extensions
source /opt/ros/jazzy/setup.bash
colcon build --base-paths world_compute_cell/ros_packages \
  --packages-select world_compute_camera --symlink-install
source install/setup.bash
```

## 3. Read it

Choose a name describing your camera, such as `desk`:

```bash
export ROS_DOMAIN_ID=87
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset ROS_STATIC_PEERS
ros2 run world_compute_camera camera_reader --ros-args \
  -p device:=/dev/video0 -p camera_name:=desk -p fps:=15.0
```

The node prints the actual image dimensions on its first frame and publishes:

```text
/cameras/desk/image_raw   sensor_msgs/Image
```

Images use BGR8 encoding and the frame ID `desk_optical_frame`. Frame timestamps
are host receipt times after reading, not measured sensor exposure timestamps.
`fps` requests a capture rate and sets the polling rate; the actual rate depends
on the camera, driver, and processing. Resolution uses the camera driver's default;
this first reader does not resize or configure calibration.

Stop with Ctrl-C to release the device. If opening or reading fails, the node exits
with an error rather than publishing an old frame. Reconnect/fix the device and
restart. There is no automatic reconnect, device scanning, or hotplug switching.

## 4. See the image

In another terminal, source ROS and the workspace and set the same ROS environment
variables as above. Install and open the ROS image viewer:

```bash
sudo apt-get install ros-jazzy-rqt-image-view
ros2 run rqt_image_view rqt_image_view
```

Select `/cameras/desk/image_raw`. On a headless host, check receipt without a GUI:

```bash
ros2 topic echo /cameras/desk/image_raw --once --field width \
  --qos-reliability best_effort
```

The publisher uses best-effort sensor-data QoS. A viewer/subscriber must support it.
Localhost discovery means the viewer must run on the same ROS host for this guide.

## Add another camera later

Run another process with its own device, camera name, and node name:

```bash
ros2 run world_compute_camera camera_reader --ros-args \
  -r __node:=side_camera_reader \
  -p device:=/dev/video2 -p camera_name:=side -p fps:=15.0
```

This publishes `/cameras/side/image_raw` with `side_optical_frame`. The node assumes
no overhead/wrist roles or fixed camera count. Choose distinct names and devices.

## What comes after reading

Calibration, CameraInfo, table-relative transforms, and MuJoCo rendering are later
layers. This direct reader publishes only images. The existing `camera_bridge`
executable is an optional adapter for our station and is not required here.

Implementation checks use mocked capture to exercise image payloads and failure
cleanup on ROS 2 Jazzy. Direct USB capture has not been hardware-tested in this
project: the available workstation's webcam remains owned by its Windows worker.
