import base64
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/world_compute_camera'))
from world_compute_camera.source import FrameSource


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'frame.json'
        self.source = FrameSource(self.path)

    def write(self, sequence=1, session='a', **changes):
        item = dict(schema_version=1, camera_id='overhead', source='windows_camera_worker',
                    session=session, sequence=sequence, captured_at=f'2026-11-26T00:00:{sequence:02d}+00:00',
                    timestamp_basis='host_wall_after_read', clock_id='windows_system_utc',
                    width=640, height=480, jpeg_base64=base64.b64encode(b'\xff\xd8test').decode())
        item.update(changes)
        self.path.write_text(json.dumps(item))

    def test_waits_for_progress_deduplicates_and_times_out(self):
        self.write(); self.assertIsNone(self.source.poll(0))
        self.write(2); self.assertIsNotNone(self.source.poll(0.2))
        self.assertIsNone(self.source.poll(0.3))
        self.assertIsNone(self.source.poll(3))
        self.assertEqual(self.source.state,'stale')

    def test_old_file_is_not_published_at_start(self):
        self.write(); self.source.poll(0); self.source.poll(3)
        self.assertEqual(self.source.state,'stale')
        self.assertFalse(self.source.started)

    def test_restart_and_reconnection(self):
        self.write(); self.source.poll(0)
        self.path.unlink(); self.assertIsNone(self.source.poll(1))
        self.assertEqual(self.source.state,'unavailable')
        self.write(session='b'); self.assertIsNone(self.source.poll(2))
        self.write(2,session='b'); self.assertIsNotNone(self.source.poll(3))

    def test_rejects_malformed_identity_time_and_image(self):
        for changes in [dict(camera_id='arm'),dict(width=0),dict(sequence=True),
                        dict(captured_at='2026-11-26T00:00:00'),dict(jpeg_base64='bad')]:
            with self.subTest(changes=changes):
                self.write(**changes); self.assertIsNone(self.source.poll(0))
                self.assertEqual(self.source.state,'unavailable')

    def test_rejects_regression_and_counts_skipped_exports(self):
        self.write(); self.source.poll(0)
        self.write(4); self.assertIsNotNone(self.source.poll(1))
        self.assertEqual(self.source.skipped,2)
        self.write(3); self.assertIsNone(self.source.poll(2))
        self.assertEqual(self.source.state,'unavailable')

    def test_bounds_file_reads(self):
        self.path.write_bytes(b'x' * 4_000_001)
        self.assertIsNone(self.source.poll(0))
        self.assertEqual(self.source.state,'unavailable')

if __name__ == '__main__':
    unittest.main()
