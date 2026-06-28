# Changelog

This project uses a simple changelog format inspired by Keep a Changelog.

## Unreleased

### Planned

- Refactor simulation into smaller modules.
- Add Traffic Simulation V1.
- Add realistic Type 1 and Type 2 charging-station model.
- Improve graphics and animations.

## 0.1.0 - Initial prototype

### Added

- React, Vite, TypeScript app scaffold from Google AI Studio.
- Top-down BEV battery bay visualisation.
- Dump truck and loader machine types.
- VPX and VPY battery types.
- Parking, work areas, queue lane, swap bays, charging/storage pads, and cranes.
- Battery SOC behaviour.
- Machine work, queue, swap, and return-to-work flow.
- Crane battery swap sequence.
- Battery charging on charger pads.
- Live KPI dashboard.
- Configurable simulation controls.
- Battery drain test tool.

### Known limitations

- Charging station model is simplified.
- Traffic simulation is not yet implemented.
- Vehicle overlap can occur.
- Movement is waypoint-based.
- Rendering and simulation logic are still tightly coupled.

## 0.1.1 - Documentation pass

### Added

- Replaced default AI Studio README with project README.
- Added docs folder.
- Added overview documentation.
- Added local run instructions.
- Added simulation model notes.
- Added architecture notes.
- Added controls and KPI documentation.
- Added roadmap.
- Added changelog.

### Notes

This documentation pass was completed before the refactor and before Traffic Simulation V1.