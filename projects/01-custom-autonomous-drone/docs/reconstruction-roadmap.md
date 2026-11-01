# Reconstruction roadmap

## What the builder remembers

Lewis describes autonomous flight with position adjustment, computer vision, path planning and geolocation. He describes a five inch racing frame, a three cell lithium polymer battery, a custom power distribution board, a Raspberry Pi 3 and an Arduino S3 mini. He recalls pressure and motion sensors, WiFi, Bluetooth and PID control.

He also describes a private wireless connection and a telemetry screen showing sensor information and the condition of the aircraft. This is the builder account. The original code, measurements and component records are not available in this workspace. The exact board, sensors, camera, radio arrangement and original network design remain unconfirmed.

## Target architecture

This is a design for a new reconstruction. It is not a statement that the original system used these exact modules or interfaces.

1. Sensor adapters capture time stamped IMU, pressure, position, camera and power readings. Each reading carries units, a source, a time and a validity state.
2. State estimation combines measurements and uncertainty. A full estimator would need position, velocity, attitude and sensor bias states. It would need a reviewed coordinate convention and explicit handling of delayed or missing measurements.
3. A mission planner turns a destination and a map into a route. A separate local planner checks obstacles, geofences and changes in the environment.
4. A controller converts an approved simulated trajectory into bounded control requests. Attitude and position loops need separate models, rates and limits.
5. A supervisor owns mode transitions and handles stale sensors, loss of position, battery faults, communication loss and conflicting commands.
6. A telemetry service publishes time stamped measurements, estimates and health states. A screen shows a value as unknown when no reliable measurement exists.
7. A simulation environment supplies sensor and vehicle models. It records configurations, seeds, fault injections and traces for repeatable tests.

## Present implementation

The vertical simulation uses a simple one dimensional model with a bounded PID style controller. It generates idealised pressure and motion readings, noisy altitude and an altitude only position signal. It does not model attitude, geographic coordinates, a camera, motors, battery behaviour or three dimensional flight.

The vertical estimator uses a two state extended Kalman filter. Its state is altitude and vertical velocity. The process uses synthetic acceleration. The filter can update from nonlinear pressure and a synthetic altitude observation. It records covariance and can reject an observation using a configured innovation threshold. A separate closed loop vertical simulation now feeds the estimated altitude and velocity into a bounded controller. It is not a full flight estimator or a three dimensional flight model.

The planner uses a synthetic two dimensional occupancy grid. It finds a shortest four direction route through clear cells. It does not create a flyable trajectory and it has no obstacle perception, aircraft dynamics or geographic coordinates.

A separate three dimensional grid planner and kinematic mission can find a route around blocked cells. The model moves at a fixed speed between grid points and pauses during a simulated position outage. The dashboard can replay this route. It is not a three dimensional dynamics model or an autonomous aircraft.

A simple detector finds bright connected regions in synthetic grayscale images. It is not a trained model and it has not been evaluated on camera images.

Telemetry snapshots expose the simulated readings and link availability flags. They mark the four motor positions, battery and geographic position as not modelled. A local read only screen can replay the closed loop simulation. There is no login, live wireless connection or command interface yet.

A separate point mass example calculates position and velocity in three axes from four prescribed upward thrust values, gravity and linear drag relative to wind. It stops at a flat ground surface. The aircraft is held level and there is no torque or attitude model. Motor loss changes total thrust but does not represent the rotation or other effects on a real aircraft. It is not connected to the estimator, route planner or controller.

## Later engineering stages

### Three dimensional simulation

Define coordinate frames, units, sensor rates, timing, vehicle dynamics and motor mixing. Introduce position, attitude and angular velocity with documented assumptions. Compare known cases with independent calculations. Add noise, bias, loss of data and model mismatch before drawing conclusions.

### Sensor fusion

Specify the state vector, process equations, measurement models, covariance and reset rules. Fuse only sensors whose timestamp, calibration and coordinate frame are known. Test missing data, delayed data, outliers and inconsistent sensors. Review numerical stability and compare the estimate with simulated ground truth. The current vertical filter is a stepping stone rather than a completed solution.

### Computer vision

Choose a concrete task and labelled dataset before selecting a method. Define the camera model, calibration, lighting conditions and failure behaviour. Test detection quality and timing on held out examples, including cases where the system must report that it cannot see a target. The simple region detector only establishes basic image processing mechanics. Camera capture, calibration and detection on real images are not implemented yet.

### Path planning and autonomy

Specify the map representation, geofence, mission states and the authority to start or stop a mission. Test route planning, blocked destinations and changing obstacles separately from control. The current grid planner has fixed obstacles and simplified motion. A route is not a verified flight trajectory. Dynamic avoidance and autonomous flight are not implemented yet.

### Telemetry and connectivity

Define a versioned telemetry schema with timestamps and explicit unknown states. Show the front left, front right, rear left and rear right only when the required sensors or measurements exist. Add access control, authentication, encryption and audit logging before connecting real systems. Protect secrets and test invalid credentials, dropped connections and stale data.

A private WiFi network is local to its radio coverage. Access from another location needs a suitable internet or cellular connection and an authenticated encrypted tunnel. Radio range and remote availability depend on hardware, terrain, interference and network coverage. No remote access service is implemented yet.

### Physical work

A physical reconstruction would require confirmed component specifications, power and thermal design, electrical protection, safe test procedures and applicable regulatory review. The software in this repository is not approved for motors or flight.

## Verification gates

The current tests verify individual functions and the stated synthetic examples. Later stages need independent mathematical checks, integration tests, recorded simulations, fault campaigns and engineering review. Hardware tests would need a separate safety plan. No finite test suite can prove every scenario or establish that an aircraft is safe to fly.
