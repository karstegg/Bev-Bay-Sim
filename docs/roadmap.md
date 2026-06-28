# Roadmap

This roadmap is intentionally practical. The goal is to grow the prototype without destroying the working simulation loop.

## Phase 0 - Current crude prototype

Status: in progress / mostly present.

- Working visual simulation.
- Machines, batteries, cranes, swap bays, charger/storage pads.
- Live KPIs.
- Configurable controls.
- Shift active/dead-time behaviour.
- Work areas with different demand multipliers.

## Phase 1 - Documentation and refactor

Status: current focus.

- Replace the default AI Studio README.
- Add documentation.
- Refactor simulation into modules.
- Preserve current visible behaviour.
- Add simple validation checks or tests if practical.

## Phase 2 - Traffic Simulation V1

Planned.

- Vehicle dimensions.
- Current speed, max speed, acceleration, and braking.
- Safe following distance.
- Stop and yield signs.
- Lane occupancy.
- Conflict zones.
- Traffic debug overlay.
- Visual stopped/braking indication.

This phase should remain simple. Do not add advanced pathfinding yet.

## Phase 3 - Real charging station model

Planned.

- Type 1 charging stations.
- Type 2 charging stations.
- Charging points separated from battery pads.
- Connection rules between charging points and pads.
- Accurate charger utilisation.
- Mini-sub and electrical capacity constraints.

Type 1 target concept:

- Four battery pads.
- Three charging points.
- One top-middle charging point can serve either top pad.
- Bottom-left charging point serves bottom-left pad.
- Bottom-right charging point serves bottom-right pad.

Type 2 target concept:

- Simpler station.
- One charging point.
- Charging point positioned on the far left or far right depending on orientation.

## Phase 4 - Graphics and animation improvement

Planned.

- Better vehicle sprites.
- Better battery icons.
- Animated crane movement.
- Better charging station graphics.
- Improved bay demarcation.
- Better status labels.
- Optional simple sound/effects.

## Phase 5 - Scenario/gameplay layer

Planned.

- Shift objectives.
- Bottleneck alerts.
- Player interventions.
- Scenario presets.
- Scorecards.
- What-if comparisons.
- Difficulty settings.

## Phase 6 - Engineering simulation layer

Planned.

- Scenario export/import.
- Monte Carlo runs.
- KPI reports.
- Parameter sweeps.
- Optional separate discrete-event engine later.
- Potential SimPy backend or equivalent if engineering analysis becomes the priority.

## Guiding rule

The prototype must remain playable at each step. Avoid large feature batches that make it impossible to tell what broke.