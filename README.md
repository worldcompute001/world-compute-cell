# I’m open-sourcing my home robotics lab! 🤖

**A robot, a few cameras, and a workspace anyone should be able to build on.**

I’m starting **world-compute-cell** to share the software and setup behind a home
robotics lab—and make it easier for other people to build their own.

The idea is simple: connect your robot, see what it sees, control it from your own
computer, and start experimenting. Then let other people join you remotely.

We’re starting with one small building block: **connect a camera and start reading it.**
Install the Python CLI, then let it prepare your Ubuntu 24.04 camera computer:

```bash
pipx install "git+https://github.com/worldcompute001/world-compute-cell.git"
world-compute cell setup
world-compute cell cameras list
world-compute cell cameras setup
world-compute cell cameras start
```

The Python package is `world-compute-cell`; the command is `world-compute`.
You can also install the same Git URL with `pip install` inside a virtual environment.
The package is not published on PyPI yet.

Choose your camera from the list and give it a name. No robot, calibration, or
preset lab setup is required. Follow the [first camera guide](docs/camera-reader.md).
The rest of the cell is being built incrementally.

## What we’re building toward

- **Control your robot locally.** See its state and camera feeds, move it, and stop
  it from a local interface. No cloud account required.
- **Give your robot a view of the workspace.** Connect cameras and calibrate where
  the table, objects, and gripper are.
- **Try experiments in simulation and on the real robot.** Run the same task in
  both places and understand where the results differ.
- **Keep a record of what happened.** Save observations, commands, and results so
  experiments can be replayed, inspected, and improved.
- **Share the lab.** Later, stream sessions and give people remote access, with
  control permissions enforced by the local cell.

A “cell” just means one robot workspace: the arm, its cameras, the table, and the
computer running it. The goal is to make that setup useful on its own and easy to
connect to others.

## Start small, build together

The first planned setup is an **SO-100 arm, two fixed cameras, a tagged block, and
a matching MuJoCo simulation**. Support for more robots, including YAM, comes later.

One early experiment: ask the gripper to hover above a block, try it in simulation
and on the table, and compare what actually happened. Getting that simple task
working reliably means bringing motion, perception, calibration, and recording
together.

## How the pieces fit

We’re designing around **ROS 2** to connect five parts of the lab:

| Part | What it does |
| --- | --- |
| Environment | Connects the real robot or runs its simulation |
| Controls | Turns a target into robot motion |
| Awareness | Tracks the objects and gripper in the workspace |
| Telemetry | Records what the robot saw and did |
| Experiment harness | Runs a task and evaluates the result |

Local operation comes first. Later, World Compute and LiveKit can connect the cell
to remote viewers and operators.

Want the technical details? Read the [architecture](docs/architecture.md) and
[roadmap](docs/roadmap.md).

## Come help shape it

If you’ve built a robot setup at home, worked with ROS 2, fought with camera
calibration, or just wanted an easier way to get started, I’d love your input.

Right now, the most useful contributions are:

- Tell us what you’d want from your own robotics lab.
- Review the design and point out missing pieces.
- Help define the interfaces between robots, cameras, controls, and experiments.
- Improve the setup plans and documentation so someone else can follow them.

[Open an issue](https://github.com/worldcompute001/world-compute-cell/issues/new/choose)
to share an idea, or read [how to contribute](CONTRIBUTING.md) before opening a PR.
The current implementation scope is ROS 2 setup and read-only camera observations.
Cell controls and simulation integration are still being designed.

## Project notes

The design started with this [robot cell architecture proposal](https://docs.google.com/document/d/1mhJU8C7p2SW1ZzIiLx38xdQSYJj1NbP9i424I0eWIvk/edit).
We’ll track architectural choices in [decision records](docs/decisions/README.md).

**License:** An open-source release is the goal. We’re still choosing the license;
no open-source license has been granted yet. We’ll settle that before accepting
external code contributions.
