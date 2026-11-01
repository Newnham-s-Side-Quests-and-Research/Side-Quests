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
