# Proposed cell architecture

## Local cell

ROS 2 is the communication layer inside a self-contained cell. A local operator
should be able to inspect robot state and cameras, issue supported commands, stop
motion, calibrate the workspace, and run recorded tasks without cloud services.
The first hardware target proposed in the brief is one SO-100, an instrumented
block, two fixed cameras, and a matching MuJoCo scene. YAM follows later.

| Component | Owns | Proposed integration |
| --- | --- | --- |
| Environment backend | Driver or simulation, sensors, clock, reset, capability description | Physical adapter and MuJoCo adapter |
| Controls | Named-frame motion goals, planning, constraints, execution feedback | MoveIt 2; separate MoveIt Servo path |
| Awareness | Timestamped object and tool estimates, validity, calibration identity | AprilTags and tf2 |
| Telemetry | Raw observations, transforms, commands, feedback, interventions, artifacts | Cell-side recording |
| Experiment harness | Trial state, preflight, reset verification, execution, scoring, finalization | ROS 2 action server |

These are responsibility boundaries, not a finalized package or process layout.
ROS distribution, deployment OS, messages, namespaces, QoS, and launch layout are
open decisions. SO-100 planning support and YAM integration require validation.

## Communication and ownership

Use topics for continuous observations and state; actions for operations with
duration, feedback, and cancellation; and services for short bounded queries.
An operator-assisted reset is a long operation with progress and timeout.

The backend owns driver access. Controls requests execution through that boundary.
The cell must enforce one command owner per physical arm across task execution
and teleoperation. The exact arbitration protocol is a design deliverable.
Cancellation requires a stop acknowledgment. Restart recovery must reconcile
controller state and ownership before accepting another command.

## Spatial and time contracts

Use the table as the shared experiment frame. Register robot bases and cameras to
it and define the tool center point for a specified jaw opening. Version camera
intrinsics, transforms, tag sizes, tool offsets, and calibration provenance.

Estimates carry observation time, clock identity, frame, source, tracking validity,
and estimator version. Repeating an old estimate must retain its observation time.
Keep encoder-derived tool poses separate from externally measured tool poses.
Record experiment time and wall time; use local monotonic time for physical command
freshness. Clock alignment and dropped observations are part of the evidence.

## Example experiment

The harness verifies readiness, starts recording, resets the selected environment,
and verifies initial conditions. It freezes an observed block pose in table
coordinates, adds 30 mm along table Z, and requests motion. It scores independently
observed tool positions during a declared hold interval.

The brief's 5 mm tolerance and one-second hold are illustrative. Measurement quality
must justify the eventual tolerance. Distinguish success, observed task failure,
unscorable observations, infrastructure error, and cancellation. Controller success
alone is insufficient to establish task success.

## Concurrent worlds

Physical and simulated backends expose matching action and observation semantics.
A mirror follows measured state. A prediction branches from a timestamped checkpoint
and evolves independently for a declared interval. Each world has its own identity
and clock. Simulation ground truth is an explicit evaluator channel.

Named physical cameras have calibrated virtual counterparts. Tracks identify world,
camera, calibration, and capture time. Changing the viewed world must never redirect
commands. An overlay is useful only once camera projection and time alignment are
validated.

## Remote access later

The proposed World Compute API handles durable submit, status, cancel, and artifacts.
Client request keys provide idempotent submission; conflicting payloads are rejected.
LiveKit Portal for ROS bridges selected video and ROS interactions into live sessions.

Remote commands still pass through local ownership and command validation. Local
teleoperation freshness checks and a watchdog govern stale inputs or disconnects.
Spectator disconnects need not interrupt autonomous runs. A physical stop remains
available independently of the viewer.
