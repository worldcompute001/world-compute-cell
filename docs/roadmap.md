# Roadmap

These are ordered milestones, not scheduled commitments.

## Now: define a contribution-ready project

- [x] Establish scope and local-first architecture summary.
- [x] Document contribution and architectural decision workflows.
- [x] Provide design issue and PR templates.
- [ ] Choose license, copyright holder, maintainers, and repository host.
- [ ] Agree on first supported station OS and ROS 2 distribution.
- [ ] Review ROS interfaces, namespaces, clocks, QoS, and ownership protocol.
- [ ] Define local operator flows and the first hardware acceptance procedure.
- [x] Open the first implementation scope: ROS 2 setup and communication checks.
- [ ] Approve cell runtime implementation separately.

## First camera observation slice

- [x] Provide a generic Linux camera reader with user-selected device and name.
- [x] Add a CLI for runtime setup, camera discovery, saved configuration, and launch.
- [ ] Validate the CLI installer and direct camera capture on a fresh Linux station.

- [x] Reuse the Windows capture owner for the overhead camera.
- [x] Publish ROS images, uncalibrated camera info, and health status.
- [x] Verify live frames and transport loss/recovery.
- [ ] Measure intrinsics and table-to-camera transform.
- [ ] Implement a matching MuJoCo camera adapter.

## Next: operate one robot locally

Bring up one cell with documented configuration. The operator can view state and
cameras, issue supported motion, and stop it. Verify command ownership, cancellation,
disconnect behavior, and recovery. Define capabilities and limits before driver work.

## Then: calibration and reproducible experiments

Validate stationary perception against held-out fixture positions at two heights.
Measure accuracy, missing observations, repeatability, settling, and unreachable
requests before choosing scoring thresholds. Run the same hover task in MuJoCo and
on hardware with versioned manifests and synchronized evidence. Exercise tracking
loss, duplicate requests, cancellation, and restart recovery.

## Later: additional robots and remote access

Add YAM through the same contracts, with independent units, limits, and calibration
validation. Add live streaming and remote access, then operator-assisted resets and
Quest teleoperation. Preserve local operation and local command authority.
