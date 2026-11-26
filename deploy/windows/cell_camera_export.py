"""Optional exporter embedded in the existing capture owner; never opens a camera."""
import base64
import json
from pathlib import Path
import threading
import time
import uuid


def start(capture, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    session = str(uuid.uuid4())

    def run():
        import cv2
        sequence = 0
        previous = None
        while True:
            try:
                frame, captured_at = capture.snapshot()
                if captured_at != previous:
                    ok, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if not ok:
                        raise ValueError('encode failed')
                    sequence += 1
                    payload = {'schema_version': 1, 'camera_id': 'overhead',
                               'source': 'windows_camera_worker', 'session': session,
                               'sequence': sequence, 'captured_at': captured_at,
                               'timestamp_basis': 'host_wall_after_read',
                               'clock_id': 'windows_system_utc',
                               'width': frame.shape[1], 'height': frame.shape[0],
                               'jpeg_base64': base64.b64encode(jpeg).decode('ascii')}
                    temporary = directory / 'frame.tmp'
                    temporary.write_text(json.dumps(payload), encoding='utf-8')
                    temporary.replace(directory / 'frame.json')
                    previous = captured_at
            except Exception:
                # An old envelope is never refreshed on failure. The reader times out.
                pass
            time.sleep(0.2)

    thread = threading.Thread(target=run, name='ros2-camera-export', daemon=True)
    thread.start()
    return thread
