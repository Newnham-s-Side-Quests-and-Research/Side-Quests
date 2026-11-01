# Project status

This record separates the builder account, the reconstruction and the evidence for each part. The original firmware, schematics and flight logs are not available in the current workspace. The current code must not be used to control a physical aircraft.

| Area | Current work | Remaining work |
| --- | --- | --- |
| Evidence | Records, hashes and rights checks have synthetic tests. | Recover any external records if they become available. Review historical claims and publication rights. |
| Vertical control | A synthetic vertical loop connects a two state estimator to a bounded PID style controller. | Define and validate three dimensional dynamics, motor response, attitude control and physical limits. |
| Sensor fusion | Synthetic pressure, altitude and motion are used in the vertical estimator. | Define frames, calibration, timing, sensor bias states and a full attitude and position estimator. Validate against independent data. |
| Mission planning | Two dimensional and three dimensional grid planners have synthetic route tests. A kinematic mission pauses when its position signal is unavailable. | Add a validated map, changing obstacles, geofences and a trajectory that accounts for vehicle dynamics. Connect planning to control only after interface review. |
| Vision | A synthetic grayscale region detector has tests. | Define the vision task and camera. Add calibration, representative labelled images, evaluation and failure handling. |
| Telemetry | A local read only screen replays synthetic vertical and grid traces. Unmodelled hardware is identified. | Define real sensor and component measurements, a versioned protocol, authentication, encryption and secure access. No real remote access service exists. |
| Battery and power | The dashboard includes a separate three cell power arithmetic example. | Confirm the pack, motor and propeller specifications. Model measured current, voltage sag, power distribution and protection after engineering review. |
| Integration | Synthetic components have repeatable tests and local demonstrations. | Connect the full system in a reviewed simulation with timing and failure handling. Hardware work needs a separate safety plan. |

The current tests establish behaviour for the cases they exercise. They do not prove all conditions, establish physical safety or reproduce the missing original flight controller. Independent engineering review is still required.
