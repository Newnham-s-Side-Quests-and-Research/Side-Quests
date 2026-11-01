# Custom Autonomous Drone

This project records an earlier drone build and develops a separate software reconstruction. The original files are not available on this computer. The reconstruction is new work and is not the original flight controller.

## What is known

Lewis describes the original aircraft as a five inch racing frame with a four cell lithium polymer battery and a custom power distribution board. His account includes a Raspberry Pi 3, an Arduino S3 mini, pressure and motion sensors, WiFi, Bluetooth and PID control. The exact board and sensor models have not been confirmed from surviving files.

## What exists here

The evidence module records claims and file hashes. It checks references and identifies files whose contents have changed. It also identifies evidence that needs a rights decision. It does not make a publication decision.

The simulation is an isolated vertical motion model. It produces an altitude signal, an idealised pressure signal and idealised motion readings. It also records simulated WiFi and Bluetooth availability. It has a bounded PID style controller and deliberately introduced signal faults. It does not operate hardware or reproduce the original firmware.

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

## Read before using the model

The architecture document explains the equations and assumptions. The verification record says what the tests cover. The evidence gaps document separates the account of the original build from new work. None of this establishes flight safety, airworthiness or the behaviour of the original hardware.
