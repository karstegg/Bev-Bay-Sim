# Architecture

## Current architecture

The current prototype is intentionally simple.

```text
src/
  App.tsx
  simulation.ts
```

### App.tsx

`App.tsx` is responsible for:

- React layout
- sidebar controls
- KPI display
- start, pause, reset controls
- speed and configuration sliders
- battery drain test tool
- canvas lifecycle
- animation frame loop
- passing the canvas context into the drawing function

### simulation.ts

`simulation.ts` currently contains several responsibilities:

- TypeScript types and interfaces
- simulation state creation
- machine movement and state transitions
- battery charging and battery position updates
- crane state-machine logic
- KPI calculation
- canvas drawing
- layout drawing
- machine, battery, crane, pad, road, and bay rendering

This is acceptable for a crude prototype, but it will become difficult to maintain as traffic simulation, vehicle dynamics, charger-station logic, and better graphics are added.

## Architectural risk

The main risk is that simulation truth, rendering, and layout coordinates become tightly coupled.

Traffic simulation will touch pathing, machine state, lane occupancy, yielding, stopping, movement speed, rendering, and debugging overlays. That will be painful if everything remains in one large file.

## Target architecture after refactor

A future refactor should preserve behaviour while splitting responsibilities.

```text
src/
  App.tsx
  sim/
    types.ts
    config.ts
    createSimulation.ts
    updateSimulation.ts
    machineLogic.ts
    batteryLogic.ts
    craneLogic.ts
    kpiLogic.ts
    movement.ts
    layout.ts
  render/
    drawSimulation.ts
    drawRoads.ts
    drawMachines.ts
    drawBatteries.ts
    drawCranes.ts
    drawStations.ts
    colors.ts
```

## Suggested responsibility split

### sim/types.ts

All TypeScript interfaces and union types.

### sim/config.ts

Default configuration values and tunable constants.

### sim/createSimulation.ts

Initial creation of machines, batteries, pads, cranes, work slots, and KPIs.

### sim/updateSimulation.ts

Main simulation tick that calls the specialised logic modules.

### sim/machineLogic.ts

Machine state transitions, work assignment, queue behaviour, swap routing, and parking/shift logic.

### sim/batteryLogic.ts

Battery SOC updates, battery positioning, charging behaviour, and battery availability rules.

### sim/craneLogic.ts

Crane state machine and battery-handling sequences.

### sim/kpiLogic.ts

KPI calculations and bottleneck detection.

### sim/movement.ts

Movement helpers, path following, speed calculations, and later acceleration/deceleration.

### sim/layout.ts

Fixed coordinates, bay layout, road definitions, pad positions, work-area positions, and future traffic-control points.

### render/*

Canvas rendering only. Rendering should read state and layout, not decide simulation truth.

## Future traffic modules

Traffic simulation should probably add:

```text
sim/trafficTypes.ts
sim/trafficLogic.ts
render/drawTrafficDebug.ts
```

Traffic logic should handle:

- lane segments
- conflict zones
- stop and yield points
- safe following distance
- vehicle blocking
- debug state

## Design rule

Simulation logic should answer: what is true?

Rendering should answer: how is that truth drawn?

The two should remain separate as the project grows.