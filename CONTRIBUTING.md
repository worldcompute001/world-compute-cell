# Contributing

## Current phase

We are defining the cell and bringing up ROS 2. Contributions cover documentation,
interface proposals, architecture review, validation plans, and the ROS 2 setup
and communication check, plus the generic camera reader, setup CLI, and optional station adapter. Other runtime
packages and hardware integration require
a separate scope decision. Documentation contributions need no hardware.

## Workflow

1. Check the architecture, roadmap, open issues, and decision records.
2. Open a design proposal for a new boundary or consequential choice. Describe the
   problem, constraints, alternatives, proposed contract, and acceptance evidence.
3. Keep each PR focused on one change. Link its issue and explain what becomes
   clearer or possible, along with any unresolved questions.
4. Update related documentation in the same PR. Label claims as proposed,
   implemented, or measured; supply evidence for measured claims.
5. Have a maintainer review before merging. Resolve disagreements in the issue;
   record accepted architectural choices in an ADR.

Small wording and broken-link fixes can go directly to a PR. Contributor assignment and review ownership are coordinated through issues. Avoid duplicating active work: comment on the relevant issue first.

## Design conventions

- Use SI units and explicit coordinate frames, timestamps, and clock identities.
- Define ownership, cancellation, failure outcomes, and recovery alongside the
  successful path. Distinguish accepted commands from observed completion.
- Keep robot-specific drivers behind capability-based contracts.
- Preserve the distinction between measured state, estimates, and simulation truth.
- Keep cloud services optional for local operation.
- Record proposals in Markdown; avoid introducing tooling solely for documentation.

## Review checklist

- Are the scope and user benefit clear?
- Are interfaces, component ownership, and assumptions explicit?
- Are failure behavior and acceptance evidence described?
- Do relative links resolve and related documents agree?
- Are example tolerances clearly marked as provisional?
- Does the change stay within the current design, ROS 2 setup, and read-only camera scope?

Never commit credentials, private station configuration, or raw identifiable camera
recordings. Use anonymized examples when explaining observations.

## Licensing

This project is licensed under the [MIT license](LICENSE). Contributions are
provided under the same license.

## Python package development

Install into a virtual environment with `python -m pip install -e .`. The public
entry point is `world-compute cell`; module execution also works with
`python -m world_compute_cell cell`. CLI code lives in `world_compute_cell/` and
bundled ROS source in `world_compute_cell/ros_packages/`.

Run `python -m unittest discover -s tests -v`. Build a wheel with
`python -m pip wheel . --no-deps --wheel-dir dist`, then test it in a clean virtual
environment from outside the repository. Verify both command help and the bundled
runtime files. ROS-specific tests under `tests/ros/` require the sourced runtime.
