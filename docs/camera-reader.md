# Connect your first camera

Start with an Ubuntu 24.04 computer and a USB camera. The CLI finds cameras, saves
your choices, and starts the reader. You do not need to configure ROS yourself.

## 1. Prepare your computer

From this repository:

```bash
./cell setup
```

This installs the dependencies and builds the camera runtime. Ubuntu may ask for
your administrator password. Run it again after pulling runtime changes to rebuild.

## 2. Find your cameras

Plug in a camera:

```bash
./cell cameras list
```

You’ll see the detected camera names and whether they are accessible. Metadata-only
devices are excluded. If nothing appears, check the connection and try again.

## 3. Choose and name one

```bash
./cell cameras setup
```

Choose a number from the list and enter a name, such as `desk` or `side`. The CLI
saves the device path, model, connection identity, and requested frame rate. It
prefers stable device paths where the operating system provides them.

Configuration is local to your user account, outside the repository. There are no
preset camera positions or models.

## 4. Start reading

```bash
./cell cameras start desk
```

The reader reports the first image's dimensions. Leave it running while other cell
components consume the images; press Ctrl-C to stop. With only one configured
camera, `./cell cameras start` selects it automatically.

A different device identity, missing permissions, or a disconnected camera produces
an error. The CLI does not silently switch to another camera. Stop other applications
that already own the device before starting a reader.

This first CLI starts image publication. A CLI-managed graphical preview is not
implemented yet. Developers can inspect the stream with the existing tools in the
[ROS integration guide](camera-reader-developer.md).

## Manage your setup

```bash
./cell cameras configured
./cell cameras remove desk
```

Removing a saved choice does not stop an already running process. For another
camera, run setup again and give it a different name, then start it in a second
terminal.

For scripts, skip the prompts with an explicit selection:

```bash
./cell cameras setup --device /dev/video0 --name desk --fps 15
./cell cameras list --json
```

`/dev/video0` is an example. Choose a device returned by the list command.

You can also put this checkout on your shell's PATH to type `cell` instead of
`./cell`. The checked-in launcher needs only Python 3; it handles the runtime
environment each time it launches the reader.

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
The CLI and runtime build are also checked in Ubuntu WSL. That workstation has no
Linux-visible camera, so a new Linux USB-camera setup still needs physical validation.
A fresh-machine run of the dependency installer has not been validated yet.
