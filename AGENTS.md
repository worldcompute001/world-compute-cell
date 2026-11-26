# Contributor instructions for coding agents

The authorized implementation scope includes ROS 2 setup and the read-only overhead
camera adapter. Reuse the existing camera owner. Robot motion, calibration changes,
and additional runtime components require explicit additional scope.
Keep smoke checks bounded and isolated from existing robot services.

Read README.md, CONTRIBUTING.md, and docs/architecture.md before making changes.
Keep proposals distinct from accepted decisions and measured capabilities. Update
related documentation together. Prefer small, focused edits and check local links.
Do not invent validated hardware behavior, performance numbers, or license terms.
