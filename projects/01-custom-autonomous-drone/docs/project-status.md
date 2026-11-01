# Project status

This record separates the builder account, the reconstruction and the evidence for each part. The original firmware, schematics and flight logs are not available in the current workspace. The current code must not be used to control a physical aircraft.

| Area | Current work | Remaining work |
| --- | --- | --- |
| Evidence | Records, hashes and rights checks have synthetic tests. | Recover any external records if they become available. Review historical claims and publication rights. |
| Vertical control | A synthetic vertical loop connects a two state estimator to a bounded PID style controller. A separate rigid body example connects a pressure based vertical filter and a position and attitude controller. Python can call a C position calculation. | Validate dynamics against an independent simulator and measured components. Extend and review control, sensing, allocation and physical limits. |
| Sensor fusion | Synthetic pressure, altitude and motion are used in the vertical estimator. The controlled rigid body example uses pressure and ideal world frame acceleration. | Define frames, calibration, timing, sensor bias states and a full attitude and position estimator. Validate against independent data. |
| Mission planning | Two dimensional and three dimensional grid planners have synthetic route tests. A controlled example follows three dimensional grid waypoints and checks a point path against static blocked cells and grid bounds. | Add a validated map, aircraft footprint, changing obstacles and a trajectory that accounts for vehicle dynamics. Review and validate planning and control interfaces. |
| Vision | A synthetic grayscale region detector has tests. | Define the vision task and camera. Add calibration, representative labelled images, evaluation and failure handling. |
| Telemetry | A local read only screen replays synthetic vertical and grid traces. Unmodelled hardware is identified. | Define real sensor and component measurements, a versioned protocol, authentication, encryption and secure access. No real remote access service exists. |
| Battery and power | The dashboard includes a separate three cell power arithmetic example. | Confirm the pack, motor and propeller specifications. Model measured current, voltage sag, power distribution and protection after engineering review. |
| Integration | A synthetic route planner, waypoint sequencer, controller, vertical filter and rigid body model run together with static obstacle checks. | Integrate the remaining components in a reviewed simulation with timing and failure handling. Hardware work needs a separate safety plan. |

The current tests establish behaviour for the cases they exercise. They do not prove all conditions, establish physical safety or reproduce the missing original flight controller. Independent engineering review is still required.
