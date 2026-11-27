"""Requires sourced ROS 2; fake capture never opens a physical device."""
import os
os.environ['ROS_DOMAIN_ID'] = '89'
os.environ['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
os.environ.pop('ROS_STATIC_PEERS', None)
import time
import unittest
from unittest.mock import patch
import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from world_compute_camera.reader import CameraReader, validate_settings


class FakeCapture:
    def __init__(self, opened=True):
        self.opened = opened
        self.released = False
        self.fail = False
        # Non-contiguous input exercises correct packed output.
        self.pixels = np.full((6, 8, 3), 42, dtype=np.uint8)[:, ::2]
    def isOpened(self): return self.opened
    def set(self, *args): return False  # Unsupported settings are advisory.
    def read(self): return (False, None) if self.fail else (True, self.pixels)
    def release(self): self.released = True


class ReaderTests(unittest.TestCase):
    def setUp(self):
        rclpy.init(args=['--ros-args','-p','device:=/dev/null','-p','camera_name:=desk'])
        self.addCleanup(lambda: rclpy.shutdown() if rclpy.ok() else None)

    def test_receives_image_on_selected_topic(self):
        capture = FakeCapture()
        with patch('world_compute_camera.reader.cv2.VideoCapture', return_value=capture):
            node = CameraReader()
        self.addCleanup(lambda: node.destroy_node() if node.capture is not None else None)
        observer = rclpy.create_node('camera_reader_test')
        self.addCleanup(observer.destroy_node)
        received = []
        observer.create_subscription(Image, '/cameras/desk/image_raw', received.append, qos_profile_sensor_data)
        deadline = time.monotonic() + 3
        while not received and time.monotonic() < deadline:
            node.read_frame()
            rclpy.spin_once(observer, timeout_sec=0.05)
        self.assertTrue(received)
        image = received[-1]
        self.assertEqual((image.width,image.height,image.step), (4,6,12))
        self.assertEqual(image.header.frame_id,'desk_optical_frame')
        self.assertEqual(image.encoding,'bgr8')
        self.assertEqual(bytes(image.data),bytes([42])*72)
        self.assertGreater(image.header.stamp.sec,0)
        capture.fail=True
        with patch.object(node.publisher,'publish') as publish:
            with self.assertRaises(RuntimeError): node.read_frame()
            publish.assert_not_called()
        node.destroy_node()
        self.assertTrue(capture.released)

    def test_failed_open_releases_capture(self):
        capture = FakeCapture(opened=False)
        with patch('world_compute_camera.reader.cv2.VideoCapture', return_value=capture):
            with self.assertRaises(RuntimeError): CameraReader()
        self.assertTrue(capture.released)

    def test_rejects_invalid_selection(self):
        for device,name,fps in [('', 'desk',15),('/dev/null','bad/name',15),
                                ('/dev/null','desk',float('nan')),('/etc/hosts','desk',15)]:
            with self.subTest(device=device,name=name,fps=fps):
                with self.assertRaises(ValueError): validate_settings(device,name,fps)


if __name__ == '__main__': unittest.main()
