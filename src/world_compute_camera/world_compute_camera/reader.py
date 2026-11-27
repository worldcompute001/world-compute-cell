"""Minimal Linux camera → ROS Image reader. No station configuration required."""
import math
from pathlib import Path
import re
import stat

import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def validate_settings(device, camera_name, fps):
    if not device:
        raise ValueError('Select a device: -p device:=/dev/video0 (use v4l2-ctl --list-devices)')
    path = Path(device)
    if not path.is_absolute() or not stat.S_ISCHR(path.stat().st_mode):
        raise ValueError('device must be an absolute Linux video device path')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', camera_name):
        raise ValueError('camera_name must start with a letter and contain letters, digits, or underscores')
    if not math.isfinite(fps) or not 0 < fps <= 120:
        raise ValueError('fps must be finite and in (0, 120]')


class CameraReader(Node):
    def __init__(self):
        super().__init__('camera_reader', namespace='/cameras')
        self.capture = None
        try:
            self.declare_parameter('device', '')
            self.declare_parameter('camera_name', 'camera')
            self.declare_parameter('fps', 15.0)
            device = self.get_parameter('device').value
            name = self.get_parameter('camera_name').value
            fps = self.get_parameter('fps').value
            validate_settings(device, name, fps)
            if self.get_parameter('use_sim_time').value:
                raise ValueError('Physical camera reader requires system time')
            self.frame_id = f'{name}_optical_frame'
            self.publisher = self.create_publisher(Image, f'{name}/image_raw', qos_profile_sensor_data)
            self.capture = cv2.VideoCapture(device, cv2.CAP_V4L2)
            if not self.capture.isOpened():
                raise RuntimeError('Cannot open camera. Check device, permissions, and whether another app owns it.')
            # Requests are advisory; publish dimensions from the actual returned image.
            self.capture.set(cv2.CAP_PROP_FPS, fps)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.first_frame = True
            self.create_timer(1.0 / fps, self.read_frame)
            self.get_logger().info(f'Reading {device}; publishing {self.publisher.topic_name}')
        except Exception:
            self.destroy_node()
            raise

    def read_frame(self):
        ok, pixels = self.capture.read()
        stamp = self.get_clock().now().to_msg()
        if not ok or pixels is None:
            # Exit rather than repeatedly publishing the last successful image.
            raise RuntimeError('Camera read failed. Reconnect/check the device, then restart this node.')
        if pixels.ndim != 3 or pixels.shape[2] != 3 or pixels.dtype.name != 'uint8':
            raise RuntimeError('Camera did not return an 8-bit BGR image')
        image = Image()
        image.header.stamp = stamp  # Host receipt after read; not hardware exposure time.
        image.header.frame_id = self.frame_id
        image.height, image.width = pixels.shape[:2]
        image.encoding = 'bgr8'
        image.is_bigendian = 0
        image.step = image.width * 3
        image.data = pixels.tobytes()
        self.publisher.publish(image)
        if self.first_frame:
            self.get_logger().info(f'First image: {image.width}x{image.height}, bgr8; timestamp is host receipt time')
            self.first_frame = False

    def destroy_node(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        return super().destroy_node()


def main():
    rclpy.init()
    node = None
    try:
        node = CameraReader()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError, RuntimeError, cv2.error) as exc:
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f'camera_reader: {exc}')
        raise SystemExit(1) from None
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
