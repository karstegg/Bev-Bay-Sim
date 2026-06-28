# Development Roadmap

## Completed
- [x] Initial Canvas-based layout and rendering (Roads, Swap Stations, Work Areas, Parking)
- [x] Machine (BEV) pathfinding and waypoint logic
- [x] Basic battery swap simulation and crane operations
- [x] Traffic controls (Stop signs, Traffic lights)
- [x] Collision avoidance and safe zone merging
- [x] Fix routing and waypoints to properly navigate to parking and access lanes
- [x] Improve simulation step calculations (sub-stepping) to support high-speed simulation (>200x) without orbital logic bugs or waypoint overshooting
- [x] Removed unused stops and adjusted parking alignment

## In Progress
- [ ] Optimize battery charging mechanics
- [ ] Implement enhanced statistics and historical logging
- [ ] Fine-tune machine avoidance and queue balancing

## Future Enhancements
- [ ] Multi-floor or expanded facility layout
- [ ] Different vehicle profiles (varied speeds and battery capacities)
- [ ] Failure simulation (e.g. swap station downtime, vehicle breakdown)
- [ ] Custom user configurations and scenario builder
