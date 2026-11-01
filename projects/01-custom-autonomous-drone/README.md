# Custom Autonomous Drone

This project records an earlier drone build and develops a separate software reconstruction. The original files are not available on this computer. The reconstruction is new work and is not the original flight controller.

## What is known

Lewis describes the original aircraft as a five inch racing frame with a three cell lithium polymer battery and a custom power distribution board. His account includes a Raspberry Pi 3, an Arduino S3 mini, pressure and motion sensors, WiFi, Bluetooth and PID control. He describes using Python and C for the custom flight controller. He also describes autonomous adjustment, computer vision, path planning, geolocation and a telemetry screen. The exact board, sensor models and division of code between devices have not been confirmed from surviving files.

## What exists here

The evidence module records claims and file hashes. It checks references and identifies files whose contents have changed. It also identifies evidence that needs a rights decision. It does not make a publication decision.

The simulation includes an isolated vertical motion model. A separate closed loop model connects synthetic pressure, position and motion readings to a vertical state estimator and a bounded PID style controller. Both models support deliberately introduced signal faults. A grid planner, synthetic image detector and telemetry mapper are also included. They do not operate hardware or reproduce the original firmware.

A separate three dimensional kinematic mission plans a route through a synthetic grid. It moves between grid points at a fixed speed and pauses when its simulated position signal is unavailable. It does not model aircraft attitude or physical flight dynamics.

A separate point mass model calculates movement in three axes using prescribed upward thrust, gravity and linear wind drag. It holds the aircraft level and does not simulate attitude or real motor failure. It is independent of the grid mission and the vertical controller.

A separate rigid body model adds a quaternion attitude, rotor moments, body angular rates and an assumed motor response. It uses illustrative parameters and can run with prescribed motor commands. It is not yet connected to the dashboard playback.

A controlled rigid body example connects a position controller and a vertical pressure filter to that model. Horizontal position and velocity and the full attitude are ideal model values. A portable C position calculation can be loaded into the Python simulation as an alternative to the Python calculation. This is a new reconstruction rather than recovered flight controller code.

A synthetic navigation example connects the voxel planner to the controlled model. It follows waypoint targets and checks the point model against static blocked cells and a bounded grid. The local dashboard can replay still air and wind scenarios. The point check does not represent the full aircraft footprint or prove a safe path.

The controlled example can also record an assumed three cell power model. It estimates current from simulated thrust, tracks charge and estimates voltage sag. These are illustrative electrical calculations. They do not limit motor thrust and they are not measurements of the original battery.

## Run the checks

From this folder run:

```powershell
python -m unittest discover -s tests -v
```

To run the illustrative scenario:

```powershell
$env:PYTHONPATH = "src"
python -m drone_archive simulate fixtures/signal-scenario.json --output results/trace.json
```

The trace and its configuration are synthetic. The gains and physical values are illustrative. They are not measurements of the original aircraft.

To run the combined synthetic demonstration:

```powershell
$env:PYTHONPATH = "src"
python -m drone_archive demo --scenario fixtures/signal-scenario.json --grid fixtures/grid-scenario.json --image fixtures/image-scenario.json --output results/demo.json
```

The report includes the simulated signals, vertical estimate, grid route, image regions and telemetry snapshots. These components do not yet operate as a closed flight control system. The image detector uses synthetic grayscale pixels rather than a camera. The position signal is altitude only. No wireless connection is opened.

## Open the local telemetry demonstration

```powershell
$env:PYTHONPATH = "src"
python -m drone_archive dashboard fixtures/closed-loop-scenario.json
```

Open the local address printed by the command. The screen replays six synthetic scenarios and shows their metrics. A run can be downloaded for inspection. The screen cannot control an aircraft. It is bound to the local machine and has no login or remote access service. The scenarios and metrics document explains what each figure means. The formulas and component candidates document records the three cell battery references and the assumptions behind the power example.

To write the closed loop trace instead:

```powershell
python -m drone_archive closed fixtures/closed-loop-scenario.json --output results/closed-loop.json
```

To run the three dimensional grid mission:

```powershell
python -m drone_archive mission3d fixtures/mission3d-scenario.json --output results/mission3d.json
```

To run the level point mass example:

```powershell
python -m drone_archive point-mass fixtures/point-mass-scenario.json --output results/point-mass.json
```

The output is synthetic and must not be used to control an aircraft.

To run the rigid body example:

```powershell
python -m drone_archive rigid-body fixtures/rigid-body-scenario.json --output results/rigid-body.json
```

To run the controlled rigid body example:

```powershell
python -m drone_archive controlled-flight fixtures/controlled-flight-scenario.json --output results/controlled-flight.json
```

To run the connected navigation example:

```powershell
python -m drone_archive navigation fixtures/navigation-scenario.json --output results/navigation.json
```

The navigation command also accepts the optional C controller library. Its output contains the full synthetic trace and waypoint events. The dashboard replay samples that trace rather than showing every integration step.

The optional C position calculation can be compiled as a shared library with a C11 compiler. For example on Windows with Zig installed:

```powershell
zig cc -std=c11 -O2 -shared flight-controller-c/position_control.c -o results/position_control.dll
python -m drone_archive controlled-flight fixtures/controlled-flight-scenario.json --controller-library results/position_control.dll --output results/controlled-flight-c.json
```

Create the results folder before compiling. To include native compilation and Python comparison in the automated suite, set `DRONE_ZIG` to the Zig executable and run the test command above. Without that setting the native checks are skipped. The executable and library are local build tools and outputs. They are not included in the project source.

The local dashboard links to a mathematical record with numbered equations and worked examples. Its assumptions are identified alongside the calculations.

## Read before using the model

The project status document lists what is implemented and what remains. The architecture document explains the equations and assumptions. The reconstruction roadmap separates the implemented components from the work still needed for autonomy, computer vision and real connectivity. The verification record says what the tests cover. The evidence gaps document separates the account of the original build from new work. None of this establishes flight safety, airworthiness or the behaviour of the original hardware.

## Browser checks

The optional browser check requires the Python Playwright package and a compatible Chromium browser. Start the local dashboard first. Set the browser executable through the `BROWSER_EXECUTABLE` environment variable if needed. Then run `python tests/browser_dashboard.py`. It checks the formulas and interactions at three screen sizes and writes screenshots to the local results folder.
