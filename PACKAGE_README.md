# World Compute Cell

A Python CLI for setting up cameras in your local robotics lab. Choose your own
camera, give it a name, and start reading it. ROS 2 runs underneath the CLI.

## Install

```bash
pipx install world-compute-cell
```

Or install with pip inside a Python virtual environment:

```bash
python -m pip install world-compute-cell
```

## Start

On your Ubuntu 24.04 camera computer:

```bash
world-compute cell setup
world-compute cell cameras list
world-compute cell cameras setup
world-compute cell cameras start
```

Setup installs system dependencies and may request your administrator password.
Camera setup lets you select a detected capture device and save its name and settings.
Start runs the selected reader until Ctrl-C. No source checkout or manual ROS setup
is required.

The CLI requires Python 3.10+. Camera runtime setup currently supports Ubuntu 24.04
and Linux-visible cameras. WSL does not automatically expose Windows webcams.
Native macOS/Windows capture, graphical CLI preview, calibration, and MuJoCo camera
rendering are not implemented yet. This is an alpha release.

[Camera guide](https://github.com/worldcompute001/world-compute-cell/blob/main/docs/camera-reader.md)
| [Repository](https://github.com/worldcompute001/world-compute-cell)
| [Issues](https://github.com/worldcompute001/world-compute-cell/issues)

Licensed under the MIT license. Copyright 2026 World Compute.
