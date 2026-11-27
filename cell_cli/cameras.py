"""Inspect Linux capture devices without starting a video stream.

Capability layout: Linux userspace-api/media/v4l/vidioc-querycap.html.
"""
from dataclasses import asdict, dataclass
import errno
import os
from pathlib import Path
import struct


@dataclass
class Camera:
    device: str
    name: str
    bus: str
    state: str
    detail: str = ''

    def to_dict(self):
        return asdict(self)


def query(device):
    import fcntl
    fd = os.open(device, os.O_RDONLY | os.O_NONBLOCK)
    try:
        data = bytearray(104)  # Linux struct v4l2_capability.
        fcntl.ioctl(fd, 0x80685600, data, True)  # VIDIOC_QUERYCAP
        _, card, bus, _, caps, device_caps, _ = struct.unpack('=16s32s32sIII12s', data)
        effective = device_caps if caps & 0x80000000 else caps
        decode = lambda b: b.split(b'\0', 1)[0].decode(errors='replace')
        return decode(card), decode(bus), bool(effective & (0x1 | 0x1000))
    finally:
        os.close(fd)


def discover(dev_root=Path('/dev'), sys_root=Path('/sys/class/video4linux')):
    aliases = {}
    # Prefer a serial-based path; topology-based paths are the next best option.
    for kind in ('by-id', 'by-path'):
        for alias in sorted((dev_root / 'v4l' / kind).glob('*')):
            aliases.setdefault(str(alias.resolve()), str(alias))
    result = []
    for device in sorted(dev_root.glob('video[0-9]*')):
        path = aliases.get(str(device.resolve()), str(device))
        try:
            name, bus, capture = query(str(device))
            if capture:
                result.append(Camera(path, name, bus, 'available'))
        except OSError as error:
            name_path = sys_root / device.name / 'name'
            name = name_path.read_text().strip() if name_path.exists() else device.name
            state = 'permission denied' if error.errno in (errno.EACCES, errno.EPERM) else 'unavailable'
            result.append(Camera(path, name, '', state, str(error)))
    return result
