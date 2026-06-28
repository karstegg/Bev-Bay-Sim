# BEV Battery Bay Simulation

A browser-based 2D simulation/game prototype for a battery-electric vehicle battery bay in an underground mining environment.

The project models the operational flow around BEV machines, batteries, swap bays, charging and storage pads, cranes, work areas, parking, and live bottleneck KPIs. It began as a quick Google AI Studio prototype and is currently a crude but playable proof of concept.

## Current status

Prototype / proof of concept.

The app is not yet an engineering-grade digital twin. It is a visual RTS/factory-simulation style sandbox intended to help explore the operating dynamics of a BEV battery bay: queueing, charged battery availability, crane utilisation, charger utilisation, work-area demand, and shift behaviour.

## Main features

- Top-down BEV battery bay visualisation.
- Dump truck and loader machine types.
- VPX and VPY battery types.
- Parking bay, work areas, queue lane, swap bays, charger/storage pads, and cranes.
- Battery state-of-charge model.
- Crane sequence for battery removal, storage, fetching, and installation.
- Batteries recharge while on charger pads.
- Live KPIs and configurable simulation controls.
- Battery drain test tool for forcing a selected machine to 0 percent SOC.

## Tech stack

- React
- TypeScript
- Vite
- HTML Canvas
- Lucide React icons

## Quick start

```bash
npm install
npm run dev
```

The development server is configured to run on port 3000.

Build and preview:

```bash
npm run build
npm run preview
```

## Documentation

- [Overview](docs/overview.md)
- [Running locally](docs/running-locally.md)
- [Simulation model](docs/simulation-model.md)
- [Architecture](docs/architecture.md)
- [Controls and KPIs](docs/controls-and-kpis.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](docs/changelog.md)

## Current limitations

- The charging bay still uses generic charger/storage pads.
- Real Type 1 and Type 2 charging station rules are not fully modelled yet.
- Charging points are not yet separate from battery pads.
- Vehicle movement is waypoint-based.
- Traffic rules, inertia, safe following distance, stop signs, yield points, and lane conflict zones are not implemented yet.
- Vehicles may overlap visually.
- Charger utilisation is still based on simplified assumptions.
- There is no backend, database, persistent save/load, or scenario file import/export.

## Development principle

Keep the prototype playable, but keep improving the structure. The next steps are documentation, refactor, traffic simulation, and then a more truthful charging-station model.
