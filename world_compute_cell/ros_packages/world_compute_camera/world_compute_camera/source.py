"""Bounded atomic-file transport, independent of ROS and image decoding."""
import base64
from datetime import datetime
import json
from pathlib import Path

MAX_ENVELOPE = 4_000_000


class FrameSource:
    def __init__(self, path, stale_seconds=2.0):
        self.path = Path(path)
        self.stale_seconds = stale_seconds
        self.session = None
        self.sequence = -1
        self.captured_at = None
        self.last_progress = None
        self.started = False
        self.state = 'waiting'
        self.rejected = 0
        self.skipped = 0

    def poll(self, now):
        try:
            with self.path.open('rb') as handle:
                raw = handle.read(MAX_ENVELOPE + 1)
            if len(raw) > MAX_ENVELOPE:
                raise ValueError('oversize envelope')
            item = json.loads(raw)
            if (item['schema_version'] != 1 or item['camera_id'] != 'overhead'
                    or item['source'] != 'windows_camera_worker'
                    or item['timestamp_basis'] != 'host_wall_after_read'
                    or item['clock_id'] != 'windows_system_utc'):
                raise ValueError('unsupported identity')
            session, sequence = item['session'], item['sequence']
            if not isinstance(session, str) or not session or type(sequence) is not int or sequence < 1:
                raise ValueError('invalid sequence')
            stamp = datetime.fromisoformat(item['captured_at'])
            if stamp.tzinfo is None:
                raise ValueError('timestamp must include timezone')
            seconds = stamp.timestamp()
            if not 0 <= seconds < 2_147_483_647:
                raise ValueError('timestamp outside ROS range')
            width, height = item['width'], item['height']
            if any(type(v) is not int or not 1 <= v <= 4096 for v in (width, height)):
                raise ValueError('invalid dimensions')
            jpeg = base64.b64decode(item['jpeg_base64'], validate=True)
            if not jpeg.startswith(b'\xff\xd8'):
                raise ValueError('invalid JPEG')
            # On start/restart, establish a baseline and wait for producer progress.
            # Never publish an old file simply because the subscriber just started.
            if session != self.session:
                self.session, self.sequence = session, sequence
                self.captured_at = seconds
                self.last_progress = now
                self.started = False
                self.state = 'waiting'
                return None
            if sequence < self.sequence:
                raise ValueError('sequence regression')
            if sequence == self.sequence:
                if now - self.last_progress > self.stale_seconds:
                    self.state = 'stale'
                return None
            if seconds <= self.captured_at:
                raise ValueError('capture timestamp regression')
            self.skipped += sequence - self.sequence - 1
            self.sequence, self.captured_at = sequence, seconds
            self.last_progress = now
            self.started = True
            self.state = 'streaming'
            return item, jpeg, seconds
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            self.rejected += 1
            self.state = 'unavailable'
            return None
