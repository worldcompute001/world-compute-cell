# world-compute-cell

An open-source robot cell that you can operate locally, with remote access added later.

**Status: project definition and design. No runtime is implemented.**
We are establishing the architecture and contribution process before writing software.

## Purpose

Make it straightforward to connect a robot and cameras, operate them through a local
interface, calibrate the workspace, and record reproducible experiments. The cell
should work without a cloud account. Physical and simulated environments should
share task and observation contracts.

ROS 2 connects the components inside the cell. Later, World Compute can provide
remote discovery, access, scheduling, and results, while LiveKit carries live
sessions. The cell remains responsible for command ownership and execution.

## Start here

- [Architecture](docs/architecture.md): components, communication, and ownership.
- [Roadmap](docs/roadmap.md): design work and future acceptance milestones.
- [Contributing](CONTRIBUTING.md): how to propose and review changes.
- [Decisions](docs/decisions/README.md): unresolved choices and decision records.

The initial reference is the [robot cell architecture proposal](https://docs.google.com/document/d/1mhJU8C7p2SW1ZzIiLx38xdQSYJj1NbP9i424I0eWIvk/edit),
dated 26 November 2026. Repository documentation is the contributor-facing summary;
proposals and illustrative thresholds are not validated capabilities.

## Contribute now

Useful first contributions include reviewing component boundaries, specifying ROS
interfaces, documenting deployment requirements, and defining hardware validation
procedures. Open a focused design proposal using the issue template, then submit a
small documentation PR. Implementation begins after maintainers explicitly open
that phase.

## License

An open-source release is the goal. The license and copyright holder are pending
maintainer selection; no open-source license has been granted yet. Resolve this
before inviting external code contributions or publishing an open-source release.
