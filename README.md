# BEV Battery Swap Simulation

This project is a React-based simulation for Battery Electric Vehicles (BEVs) utilizing battery swap stations. The simulation handles vehicle routing, battery swapping logic, queuing, crane operations for swapping, and shift-based operational scheduling.

## Features

- **Real-Time Simulation engine:** Handles vehicle movement, pathfinding, collision avoidance, and state transitions.
- **Battery Swap Operations:** Dual swap stations (SB1 & SB2) with traffic light controls.
- **Crane Mechanics:** Simulates battery transfer cranes between charging racks and swap bays.
- **High-Speed Simulation Support:** Sub-step logic allows the simulation to scale up speeds without skipping waypoints or getting vehicles stuck.
- **Dynamic Routing:** Intelligent routing from working areas to queue lanes, parking bays, and swap bays.
- **Performance Tracking:** Tracks key performance indicators (KPIs) like active vehicles, queued tasks, and total swaps.

## Tech Stack

- React 18
- TypeScript
- Vite
- HTML5 Canvas for rendering (`src/render/`)

## Getting Started

1. Install dependencies: `npm install`
2. Start the development server: `npm run dev`
3. Build for production: `npm run build`
