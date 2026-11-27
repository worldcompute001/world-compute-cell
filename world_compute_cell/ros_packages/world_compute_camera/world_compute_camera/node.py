"""Publish physical camera observations; no device or robot control."""
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CameraInfo
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from .source import FrameSource


class CameraBridge(Node):
    def __init__(self):
        super().__init__('camera_bridge', namespace='/real/cameras/overhead')
        self.declare_parameter('source_file', '')
        self.declare_parameter('stale_seconds', 2.0)
        path = self.get_parameter('source_file').value
        stale = self.get_parameter('stale_seconds').value
        if not path or not 0 < stale <= 30:
            raise ValueError('source_file and a stale_seconds value in (0, 30] are required')
        if self.get_parameter('use_sim_time').value:
            raise ValueError('Physical bridge requires wall time; use a separate simulation adapter')
        self.source = FrameSource(path, stale)
        self.frame_id = 'real_overhead_optical_frame'
        self.images = self.create_publisher(Image, 'image_raw', qos_profile_sensor_data)
        self.info = self.create_publisher(CameraInfo, 'camera_info', qos_profile_sensor_data)
        self.status = self.create_publisher(DiagnosticArray, 'status', 10)
        self.published = 0
        self.decode_errors = 0
        self.create_timer(0.1, self.poll)
        self.create_timer(0.5, self.publish_status)

    def poll(self):
        result = self.source.poll(time.monotonic())
        if result is None:
            return
        item, jpeg, stamp = result
        pixels = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if pixels is None or pixels.shape[:2] != (item['height'], item['width']):
            self.decode_errors += 1
            self.source.state = 'invalid_image'
            return
        image = Image()
        image.header.frame_id = self.frame_id
        image.header.stamp.sec = int(stamp)
        image.header.stamp.nanosec = int((stamp - int(stamp)) * 1e9)
        image.height, image.width = pixels.shape[:2]
        image.encoding = 'bgr8'
        image.is_bigendian = 0
        image.step = image.width * 3
        image.data = pixels.tobytes()
        info = CameraInfo()
        info.header = image.header
        info.width, info.height = image.width, image.height
        # Zero matrices explicitly mean uncalibrated. Do not fabricate intrinsics/TF.
        self.images.publish(image)
        self.info.publish(info)
        self.published += 1

    def publish_status(self):
        message = DiagnosticArray()
        message.header.stamp = self.get_clock().now().to_msg()
        status = DiagnosticStatus()
        status.name = 'real/cameras/overhead'
        status.hardware_id = 'windows_camera_worker/overhead'
        status.message = self.source.state
        status.level = DiagnosticStatus.WARN if self.source.state == 'streaming' else DiagnosticStatus.ERROR
        values = {'world': 'real', 'camera_id': 'overhead', 'calibration_id': 'unavailable',
                  'calibrated': 'false', 'timestamp_basis': 'host_wall_after_read',
                  'source_clock': 'windows_system_utc', 'clock_alignment': 'unverified',
                  'status_clock': 'ros_system_time', 'published': str(self.published),
                  'rejected': str(self.source.rejected), 'decode_errors': str(self.decode_errors),
                  'export_sequences_skipped': str(self.source.skipped),
                  'capture_drops': 'unknown'}
        status.values = [KeyValue(key=k, value=v) for k, v in values.items()]
        message.status = [status]
        self.status.publish(message)


def main():
    rclpy.init()
    node = CameraBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
