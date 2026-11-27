# Architecture decisions

Use an architecture decision record (ADR) for a consequential choice spanning
components. Copy [the template](template.md) into `NNNN-short-title.md`, link the
proposal issue, and start with **Proposed**. Maintainer approval changes it to
**Accepted**. Preserve superseded records and link their replacements.

No ADRs have been accepted yet. The architecture summary captures the source
proposal, not a claim that every integration choice has been finalized.

Initial decisions to resolve:

- Maintainer and review ownership (MIT license selected).
- Station OS, ROS 2 distribution, and installation model.
- Component/package boundaries and ROS interface ownership.
- Frames, clocks, namespaces, and QoS.
- Command arbitration, cancellation, and restart recovery.
- Recording format, manifest schema, and artifact retention.
