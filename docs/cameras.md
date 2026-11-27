# Optional Windows station camera bridge

**Starting with your own camera?** Use the [generic camera reader](camera-reader.md).
This page documents our existing station adapter; it is not the default setup.

The first camera adapter reads the existing Windows worker's overhead C920 stream.
It runs in ROS 2 Jazzy on Ubuntu WSL and never opens a camera or controls a robot.

## Interface

| Topic | Message | Meaning |
| --- | --- | --- |
| `/real/cameras/overhead/image_raw` | `sensor_msgs/Image` | Decoded BGR8 image, currently 960×540 |
| `/real/cameras/overhead/camera_info` | `sensor_msgs/CameraInfo` | Same dimensions, timestamp, and optical frame; currently uncalibrated |
| `/real/cameras/overhead/status` | `diagnostic_msgs/DiagnosticArray` | Availability, calibration state, clock provenance, counters |

Images and camera info use sensor-data QoS (best effort, volatile). Status uses
reliable delivery with depth 10. The optical frame is `real_overhead_optical_frame`.
There is no table-relative TF yet. Camera matrices remain zero, the standard
[uncalibrated CameraInfo convention](https://github.com/ros2/common_interfaces/blob/jazzy/sensor_msgs/msg/CameraInfo.msg).
Streaming status is WARN until calibration exists; unavailable/stale input is ERROR.

`image_raw` contains decoded pixels, but its upstream transport is lossy JPEG and
its source is resized by the existing worker. It is not original sensor Bayer data.
Calibration must match that actual 960×540 output and any crop/distortion treatment.

## Existing capture owner → atomic file → ROS

The Windows camera worker already owns the webcam, recording, and live-streaming
paths. [cell_camera_export.py](../deploy/windows/cell_camera_export.py) adds a daemon
thread to that process and calls its existing `snapshot()` method. It exports at
most five unique frames per second. It does not open another camera.

Each frame is one bounded JSON envelope containing JPEG bytes, dimensions, source
identity, producer session, sequence, original timestamp, and clock provenance.
The exporter writes a temporary file then atomically replaces `frame.json`.
The WSL reader reads only the latest envelope; it never builds a frame backlog.

The deployment uses a read-only drvfs mount of the export directory. Credentials
are not in that directory. Windows ACLs restrict the directory to the camera
operator, administrator/SYSTEM, and the station account (read-only). These
host-specific adapter details are separate from the ROS camera contract.

A new reader or producer session waits for sequence progress before publishing.
Duplicate frames are not republished. Missing/malformed input reports unavailable;
a frozen sequence reports stale after two seconds. Progress resumes automatically.
A decode failure does not publish an image. Skipped export sequences are counted;
physical camera drops cannot be inferred and are reported as unknown.

## Timestamps and limits

Image and CameraInfo retain the worker's Windows UTC timestamp, taken after frame
read/processing. This is **not a hardware exposure timestamp**. Status identifies
`host_wall_after_read`, `windows_system_utc`, and unverified clock alignment.
Status-message headers use the ROS host's clock. Freshness uses local monotonic
producer-progress checks; it does not claim a measured end-to-end exposure age.
Cross-clock alignment and exposure timing need validation before paired sim/real
scoring. A timestamp regression is rejected until the producer catches up or starts
a new session.

## Build and run

On Ubuntu 24.04 with ROS 2 Jazzy installed:

```bash
sudo apt-get install --no-install-recommends python3-opencv python3-colcon-common-extensions
source /opt/ros/jazzy/setup.bash
colcon build --packages-select world_compute_camera --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=87
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset ROS_STATIC_PEERS
ros2 run world_compute_camera camera_bridge --ros-args \
  -p source_file:=/mnt/wc-camera-export/frame.json
```

Use domain 87 only for this local cell. The source path is configurable; invalid or
missing frames result in diagnostic status. `use_sim_time` is rejected by this
physical adapter. A calibration loader is not implemented yet.

## Station deployment and rollback

The installed package workspace is `/opt/world-compute-cell`. Windows exports to
`C:\ProgramData\WorldComputeCell\camera-export`, mounted read-only at
`/mnt/wc-camera-export`. The worker imports the exporter after starting its overhead
capture. The original worker was saved beside it as `worker.py.before-cell-camera`.
The existing camera task was restarted to load the exporter; its other code was
preserved. No recent active recording file was observed before the restart.

The [mount unit](../deploy/systemd/wc-cell-camera-source.service) and
[ROS unit](../deploy/systemd/wc-cell-camera.service) are installed and enabled in WSL.
They are station-specific examples, not a generic installer. The Windows camera
worker must already be running. No full Windows reboot acceptance is claimed.

Rollback: stop and disable `wc-cell-camera.service`, then stop and disable
`wc-cell-camera-source.service`. Restore the saved Windows worker and restart its
camera task after checking for active recording. Verify the existing camera worker
has actually exited before restarting: this station had an orphaned camera process
that stopping the scheduled task alone did not terminate. Preserve the single-owner
lock and terminate only the verified camera process tree. Remove the optional
exporter and its export directory after consumers stop. No robot service restart
is needed.

## Verification

```bash
python3 -m unittest discover -s tests -v
# Source ROS and the built workspace first; this test selects isolated domain 88.
python3 scripts/check-camera.py /mnt/wc-camera-export/frame.json
```

The integration check uses actual camera frames copied into a temporary transport.
It checks image encoding and payload size, pairs CameraInfo by timestamp, freezes
input to verify stale handling without duplicate publication, then resumes it.
It does not disconnect the physical webcam or interrupt the production stream.
Do not run two copies of this check concurrently on the same host/domain.

Verified 26 November 2026: six source tests passed. Live acceptance received 33
unique 960×540 image/CameraInfo pairs, detected stale transport, and recovered.
The overhead scene was visually inspected. The persistent service was subsequently
checked separately: 21 frames over a six-second observation, approximately 3.77 Hz
between received frames. This is one measurement, not a throughput guarantee.
Existing robot services remained active. Intrinsics, TF,
hardware unplug/replug, and cross-host clock synchronization remain unverified.

## MuJoCo next

A separate renderer adapter will publish the same image/CameraInfo contract under
`/mirror/cameras/overhead` or `/prediction/cameras/overhead`, with distinct optical
frame IDs and simulation timestamps. It must derive intrinsics from the actual
projection, publish simulation clock provenance, and keep evaluator ground truth
separate. Match pose, projection, crop, resolution, and distortion treatment before
claiming real/sim image alignment. There is no MuJoCo camera implementation yet.
