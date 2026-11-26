#!/usr/bin/env python3
"""Read live frames through a temporary transport, then inject loss and recovery."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CameraInfo
from diagnostic_msgs.msg import DiagnosticArray


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_file', type=Path)
    args = parser.parse_args()
    os.environ["ROS_DOMAIN_ID"] = "88"
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"
    os.environ.pop("ROS_STATIC_PEERS", None)
    rclpy.init()
    observer = rclpy.create_node('camera_acceptance_observer')
    images, infos, statuses = {}, {}, []
    def key(msg):
        return msg.header.stamp.sec, msg.header.stamp.nanosec
    def on_image(msg):
        assert msg.encoding == 'bgr8' and msg.step == msg.width * 3
        assert len(msg.data) == msg.height * msg.step
        assert msg.header.frame_id == 'real_overhead_optical_frame'
        images[key(msg)] = (msg.width, msg.height, time.monotonic())
    def on_info(msg):
        assert msg.k[0] == 0 and msg.header.frame_id == 'real_overhead_optical_frame'
        infos[key(msg)] = (msg.width, msg.height)
    observer.create_subscription(Image, '/real/cameras/overhead/image_raw', on_image, qos_profile_sensor_data)
    observer.create_subscription(CameraInfo, '/real/cameras/overhead/camera_info', on_info, qos_profile_sensor_data)
    observer.create_subscription(DiagnosticArray, '/real/cameras/overhead/status',
                                 lambda msg: statuses.append(msg.status[0].message), 10)
    with tempfile.TemporaryDirectory() as directory:
        copy = Path(directory) / 'frame.json'
        copy.write_bytes(args.source_file.read_bytes())
        log = open(Path(directory) / 'node.log', 'w')
        process = subprocess.Popen(['ros2','run','world_compute_camera','camera_bridge',
                                    '--ros-args','-p',f'source_file:={copy}'],
                                   stdout=log, stderr=log, start_new_session=True)
        def phase(seconds, forward):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                if forward:
                    temp = Path(directory) / 'frame.tmp'
                    temp.write_bytes(args.source_file.read_bytes())
                    temp.replace(copy)
                rclpy.spin_once(observer, timeout_sec=0.05)
                assert process.poll() is None, 'bridge exited'
        try:
            phase(6, True)
            assert len(images) >= 10 and 'streaming' in statuses, 'live frames missing'
            phase(3, False)
            assert statuses[-1] == 'stale', statuses[-1]
            frozen = len(images)
            phase(1, False)
            assert len(images) == frozen, 'republished stale frame'
            phase(3, True)
            assert len(images) > frozen + 5 and statuses[-1] == 'streaming', 'recovery failed'
            matched = set(images) & set(infos)
            assert len(matched) >= 10, 'image/camera_info pairing failed'
            for stamp in matched:
                assert images[stamp][:2] == infos[stamp]
            ordered = sorted(images)
            assert all(b > a for a, b in zip(ordered,ordered[1:]))
            print(json.dumps({'result':'PASS', 'unique_images':len(images),
                              'matched_camera_info':len(matched),
                              'dimensions':images[ordered[-1]][:2],
                              'stale_transport':'detected; no old images republished',
                              'recovery':'passed', 'calibrated':False}))
        finally:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            log.close()
            observer.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
