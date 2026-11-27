# Connect your first camera

Start with an Ubuntu 24.04 computer and a USB camera. The CLI finds cameras, saves
your choices, and starts the reader. You do not need to configure ROS yourself.

## 1. Install the Python package

On Ubuntu 24.04, install pipx and Git if needed:

```bash
sudo apt-get install pipx git
pipx ensurepath
```

Open a new terminal, then install:

```bash
pipx install "git+https://github.com/worldcompute001/world-compute-cell.git"
```

Alternatively, inside a Python virtual environment:

```bash
python -m pip install "git+https://github.com/worldcompute001/world-compute-cell.git"
```

The package is called `world-compute-cell` and installs the `world-compute` command.
It currently installs from GitHub; it is not published on PyPI. Python 3.10 or newer
is required for the CLI. Camera runtime setup currently supports Ubuntu 24.04.

## 2. Prepare your computer

From any directory:

```bash
world-compute cell setup
```

This installs the dependencies and builds the camera runtime. Ubuntu may ask for
your administrator password. After upgrading the Python package, run setup again to build its camera runtime.
The package bundles the necessary sources; a source checkout is not required.

## 3. Find your cameras

Plug in a camera:

```bash
world-compute cell cameras list
```

You’ll see the detected camera names and whether they are accessible. Metadata-only
devices are excluded. If nothing appears, check the connection and try again.

## 4. Choose and name one

```bash
world-compute cell cameras setup
```

Choose a number from the list and enter a name, such as `desk` or `side`. The CLI
saves the device path, model, connection identity, and requested frame rate. It
prefers stable device paths where the operating system provides them.

Configuration is local to your user account, outside the repository. There are no
preset camera positions or models.

## 5. Start reading

```bash
world-compute cell cameras start desk
```

The reader reports the first image's dimensions. Leave it running while other cell
components consume the images; press Ctrl-C to stop. With only one configured
camera, `world-compute cell cameras start` selects it automatically.

A different device identity, missing permissions, or a disconnected camera produces
an error. The CLI does not silently switch to another camera. Stop other applications
that already own the device before starting a reader.

This first CLI starts image publication. A CLI-managed graphical preview is not
implemented yet. Developers can inspect the stream with the existing tools in the
[ROS integration guide](camera-reader-developer.md).

## Manage your setup

```bash
world-compute cell cameras configured
world-compute cell cameras remove desk
```

Removing a saved choice does not stop an already running process. For another
camera, run setup again and give it a different name, then start it in a second
terminal.

For scripts, skip the prompts with an explicit selection:

```bash
world-compute cell cameras setup --device /dev/video0 --name desk --fps 15
world-compute cell cameras list --json
```

`/dev/video0` is an example. Choose a device returned by the list command.

The CLI handles the runtime environment every time it launches the reader.
Use `world-compute --version` or `world-compute cell --help` to inspect the installed CLI.

## Current support

- Automatic setup: Ubuntu 24.04, using ROS 2 Jazzy internally.
- Capture: Linux-visible video devices supported by OpenCV's V4L2 backend.
- WSL: Windows webcams need a Linux device attachment or a separate adapter.
  The existing [Windows station bridge](cameras.md) is one such adapter, and is
  independent of the generic CLI.
- Native macOS/Windows capture, calibration, simulation, and automatic reconnect
  are future work.

Camera configuration is stored in `~/.config/world-compute-cell/cameras.json`
(or under `XDG_CONFIG_HOME`). Frames are published locally, not uploaded. Starting
readers through this CLI prevents duplicate CLI owners for the same device within
the same user account; it cannot arbitrate unrelated capture applications.

## Verification status

Device selection, stable path preference, metadata filtering, configuration writes,
identity-change rejection, and runtime command construction have automated tests.
A wheel was installed into fresh Python environments outside the checkout; the
installed package built and loaded its bundled ROS runtime in Ubuntu WSL. That workstation has no
Linux-visible camera, so a new Linux USB-camera setup still needs physical validation.
The release workflow also passed on a fresh Ubuntu 24.04 runner: dependency installation,
bundled runtime build, and three ROS tests covering image delivery and failure handling
with a simulated capture device. These checks do not validate a physical USB camera.

## Package and runtime storage

The pip package contains the CLI and the ROS camera source. `world-compute cell setup`
copies the source into a runtime workspace under
`~/.local/share/world-compute-cell/runtimes/` (or `XDG_DATA_HOME`) and builds there.
The workspace is keyed by the bundled source contents, so upgrades do not overwrite
a runtime used by an existing process. Old runtime directories can be removed after
their readers have stopped. Configuration remains in the same per-user config file
across package upgrades.

ROS uses Ubuntu's system Python internally, independently of the Python environment
used to install the CLI. Installing the pip package alone does not install OS packages
or change camera services; the explicit setup command installs dependencies.
