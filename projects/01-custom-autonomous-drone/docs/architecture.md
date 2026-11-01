# Architecture and design decisions

## Evidence

The evidence module validates a versioned register. Each artefact has an identifier, a SHA256 hash, a source and a rights state. A claim has a status, evidence references, a reviewer, a date and a rationale. A claim described as flown, bench tested, simulated or conceptual needs at least one evidence reference. A reference is not proof of the claim by itself.

File verification takes an explicit root directory. It compares recorded hashes with files under that root and reports missing, changed or inaccessible material. Paths that resolve outside the root are rejected. A publication manifest lists cleared artefacts and flags unsupported claims. A person still decides whether anything can be published.

## Illustrative signal model

The simulation models altitude and vertical velocity only. Its state update uses explicit Euler integration:

```text
acceleration = (thrust - mass * gravity - drag * velocity) / mass
next altitude = altitude + velocity * timestep
next velocity = velocity + acceleration * timestep
```

A simple PID style controller uses altitude error, an accumulated error and ideal simulated velocity. The thrust command is bounded. The integral is held when the proposed command is saturated in the direction of the error and when the altitude signal is missing. This convention is part of the model, not a claim about the original controller.

A seeded synthetic altitude signal supports noise, bias and missing samples. The model also emits idealised pressure using an exponential atmosphere and an ideal vertical accelerometer signal. The angular rate is zero because rotation is not modelled. WiFi and Bluetooth are availability flags with specified outage windows. They do not open network connections.

Fault windows include the start step and exclude the end step. A noise sample is drawn at every step, including a missing sample, so the random sequence stays aligned when comparing a run with and without an outage.

The pressure, IMU and link signals are synthetic observables. The controller uses the altitude signal and ideal simulated velocity. It does not use the pressure or IMU outputs as a flight controller would. The model does not include a four cell battery, motor response, frame geometry, attitude, wind, ground contact or flight dynamics in three dimensions.

## Decisions still open

The exact microcontroller and sensor models, wiring, calibration, sampling rates, original controller gains and firmware interfaces are unknown. The reported name Arduino S3 mini needs clarification before selecting a specific board. A real reconstruction needs its own requirements and engineering review. The example gains and sensor assumptions are not a basis for physical flight.

## Vertical estimation

A separate two state extended Kalman filter estimates altitude and vertical velocity. Its prediction uses a specified acceleration variance. Its pressure observation uses the derivative of the exponential pressure model. A scalar altitude observation represents a simplified GPS reading. The covariance update uses Joseph form and a configurable innovation limit can reject an outlier.

The replay uses simulated pressure, altitude observations and ideal simulated acceleration. The GPS signal contains altitude only. In the original replay the estimator does not feed the controller. A separate closed loop simulation uses estimated altitude and velocity as controller inputs. Neither model represents a full sensor fusion system.

## Planning and telemetry

The planner uses A star on a bounded two dimensional grid with four possible movements. It returns a shortest route or no route. It has no representation of aircraft motion or real coordinates. The telemetry mapper converts synthetic samples to read only snapshots. Motor, battery and geographic position states remain explicitly unmodelled. It opens no network connection.

## Synthetic vision and integration

A separate image module finds connected regions above a brightness threshold in a synthetic grayscale grid. It reports area, bounding coordinates and centroid. It rejects malformed images and does not claim to recognise objects in a real camera feed.

The integration demonstration runs the synthetic signal model, vertical estimator, grid planner, image detector and telemetry mapper from recorded fixture configurations. It stores the input fixtures, estimator settings and output traces. The modules are demonstrated together but are not connected in a closed flight control loop.

## Closed loop and local dashboard

The closed loop model samples synthetic pressure and position readings before each control step. The estimator updates from accepted observations. A PID style controller uses the estimated vertical state. The plant then advances and its synthetic acceleration is used for prediction. Noise comes from independent seeded generators.

Before the first accepted observation the model remains in a degraded state. It also enters that state if observations are unavailable for more than the configured number of steps or the synthetic motion signal is missing. It uses zero thrust as a test convention and holds the integral. The estimator uses a zero mean acceleration assumption with increased process variance while the motion signal is unavailable. These choices are not flight safety procedures.

The dashboard is a local read only view of one generated trace. It binds only to the local machine and does not open a connection to hardware. A component is shown as not modelled when the simulation has no data for it. The view has no authentication or remote service.
