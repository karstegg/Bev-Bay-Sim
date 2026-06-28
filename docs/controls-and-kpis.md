# Controls and KPIs

## Controls

### Start / pause

Starts or pauses the simulation loop.

### Reset

Recreates the simulation from the current configuration.

### Simulation speed

Controls the simulation multiplier. Current options are 1x, 2x, and 5x.

### Arrival rate / depletion multiplier

Currently acts as a general demand/depletion multiplier. Higher values make batteries discharge faster during work, increasing return-to-bay demand.

### VPX charge time

Controls how long VPX batteries take to charge from empty to full in the simplified model.

### VPY charge time

Controls how long VPY batteries take to charge from empty to full in the simplified model.

### DT discharge rate

Controls how quickly dump truck batteries discharge. Lower values mean faster discharge.

### FL discharge rate

Controls how quickly loader batteries discharge. Lower values mean faster discharge.

### DT speed

Controls dump truck movement speed in the current waypoint movement model.

### FL speed

Controls loader movement speed in the current waypoint movement model.

### Dead time hours

Defines the inactive portion of the simulated day. During dead time machines park instead of continuing production.

### Work area split percentages

Controls the probability that machines are assigned to each of the four work areas.

### Work area depletion multipliers

Controls how demanding each work area is. Higher multipliers cause faster battery depletion for machines assigned to that area.

### Swap time

Controls the time used by the crane sequence to remove and install batteries.

### Active cranes

Controls how many cranes are available for battery handling.

### Spare batteries

Controls the starting number of spare batteries. Changing this requires a reset because the simulation state must be recreated.

### Show labels

Toggles object labels in the visual display.

### Show legend

Toggles the visual legend.

### Battery drain test tool

Allows a selected BEV machine to be forced to 0 percent SOC. This is useful for testing routing, queueing, and battery swap logic.

## KPIs

### Waiting

Number of machines currently travelling to the queue or waiting in the queue.

### Served

Number of machines that have completed a battery swap and left the swap bay.

### Avg Wait

Average current waiting time for machines in the queue.

### Avg Turnaround

Average turnaround metric based on completed swap cycles. This may need refinement later to separate travel time, queue time, and swap time.

### Charged Ready

Number of fully charged batteries available on pads.

### Charging

Number of batteries currently charging on charger pads.

### Depleted Wait

Number of depleted or partially charged batteries waiting on storage pads rather than charging.

### Charger Utilisation

Current simplified charger utilisation. This is currently based on charger pads, not yet on a realistic charging-point model.

### Crane Utilisation

Percentage of active cranes currently busy.

### System Bottleneck

A simple bottleneck diagnosis based on queue size, charged battery availability, crane utilisation, charger saturation, and pad availability.

## KPI caveat

The KPI formulas are useful for the prototype but should evolve as the physical bay model becomes more realistic.

In particular, charger utilisation should eventually be calculated from actual active charging points, not simply from generic charger pads.