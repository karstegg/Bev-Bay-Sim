# Overview

BEV Battery Bay Simulation is a browser-based 2D prototype for exploring the operation of a battery-electric vehicle battery bay in an underground mine.

The simulator is deliberately game-like. It uses a top-down RTS/factory-simulation view so that the operating flow is visible: machines leave parking, work, discharge batteries, return to the bay, queue, swap batteries, and return to work.

## Why this exists

Battery-electric mining fleets move the bottleneck from diesel refuelling and ventilation toward battery logistics, charging capacity, bay layout, traffic flow, and battery availability.

The core operational question is simple:

> Can the battery bay supply charged batteries fast enough to keep BEV machines productive?

That question depends on charger count, battery stock, crane availability, swap time, queueing, traffic, and the physical arrangement of the bay.

## Mining context

The model represents a simplified underground BEV battery bay. Machines are represented as dump trucks and loaders. Batteries are represented as VPX and VPY types. Cranes or handlers perform the physical swap sequence. Charger and storage pads represent the current simplified charging bay.

The simulator is not yet a digital twin. It is a prototype used to reason about operations and to develop a playable visual demo.

## Prototype versus engineering simulator

The current app is a visual prototype first. It is useful for seeing flow, congestion, and bottleneck behaviour.

An engineering-grade simulator would need more rigorous assumptions, validated cycle times, real charger capacities, Type 1 and Type 2 charging-station logic, traffic rules, scenario import/export, and repeatable reporting.

The intended direction is to grow from this visual prototype toward a more defensible simulation model without losing the game-like clarity.