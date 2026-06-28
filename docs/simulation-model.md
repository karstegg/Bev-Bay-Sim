# Simulation model

This document describes the current simplified model. It should be updated whenever the simulation rules change.

## Main entities

### Machine

A BEV machine represents a production vehicle. The current machine types are:

- `DT` - dump truck
- `FL` - loader / LHD

Each machine has a current state, position, battery assignment, work area, queue information, and movement path.

### Battery

A battery has:

- battery type
- state of charge
- current state
- current position
- assigned machine or pad
- reservation information

Current battery types:

- `VPX`
- `VPY`

The simplified mapping is:

- DT machines use VPX batteries.
- FL machines use VPY batteries.

### Pad

Pads are fixed battery positions. Current pad types are:

- `charger`
- `storage`

This is a simplification. Future versions should separate physical battery pads from charging points.

### SwapBay

A swap bay is a location where a machine receives a battery swap. The current model has two swap bays.

### Crane

A crane represents a battery-handling unit. It removes depleted batteries, stores them, fetches charged batteries, and installs them into machines.

### WorkSlot

A work slot represents a simplified productive work location in one of the work areas.

### SimState

The full simulation state contains time, machines, batteries, pads, swap bays, cranes, work slots, configuration, and KPIs.

### SimConfig

The configuration controls speed, active cranes, charge/discharge times, work-area split, work-area depletion multipliers, dead time, swap time, and starting spare batteries.

### SimKPIs

KPIs track waiting machines, served machines, waiting time, turnaround time, charged batteries, charging batteries, depleted waiting batteries, charger utilisation, crane utilisation, bottleneck, and simulated time of day.

## Machine states

Current machine states:

- `parked`
- `driving_to_work`
- `working`
- `driving_from_work`
- `driving_to_queue`
- `in_queue`
- `driving_to_swap`
- `at_swap`
- `driving_away`
- `driving_to_park`

## Battery states

Current battery states:

- `in_machine`
- `on_pad`
- `held_by_crane`

## Crane states

Current crane states:

- `idle`
- `moving_to_remove`
- `removing`
- `moving_to_store`
- `storing`
- `moving_to_fetch`
- `fetching`
- `moving_to_install`
- `installing`
- `moving_to_fetch_for_charge`
- `fetching_for_charge`
- `moving_to_charge`
- `storing_for_charge`

## High-level simulation loop

1. Machines leave parking and go to work during active shift time.
2. Batteries discharge while machines work.
3. Low-SOC machines return to the battery bay.
4. Machines enter the queue.
5. If a suitable fully charged battery and swap bay are available, the front machine is assigned to a swap bay.
6. A crane removes the depleted battery.
7. The crane stores the depleted battery on a charger or storage pad.
8. The crane fetches the assigned charged battery.
9. The crane installs the charged battery.
10. The machine leaves the swap bay and returns to work.
11. Batteries on charger pads recharge over time.
12. During dead time, machines park instead of continuing production.

## Current simplifications

- Charger pads are simplified.
- Type 1 and Type 2 charging station rules are not fully represented yet.
- Charging points are not separate resources.
- Vehicle movement is waypoint-based.
- Traffic rules are not implemented yet.
- Vehicles may overlap visually.
- No advanced pathfinding is implemented.
- No persistent scenario save/load exists.
- No backend or database exists.
- KPI formulas may need revision as the physical model becomes more truthful.