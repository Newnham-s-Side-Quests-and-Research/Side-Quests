# Formulas and component candidates

## Battery reference

Lewis corrected the earlier account to a three cell lithium polymer pack. For a standard LiPo chemistry with three cells in series:

```text
Nominal pack voltage = 3 cells × 3.7 volts per cell = 11.1 volts
Full charge reference = 3 cells × 4.2 volts per cell = 12.6 volts
```

These are chemistry reference values. Actual pack voltage depends on charge, load, temperature and cell condition. Pack voltage alone does not reliably establish remaining capacity. The exact original pack capacity and cell condition are unknown.

The dashboard uses an illustrative 1500 mAh capacity with a fixed voltage of 11.1 V and a fixed current of 8 A. These are inputs for arithmetic, not measurements or recommended operating values. Voltage is held at the nominal reference. The model does not infer state of charge from voltage. The power calculation is not connected to motor thrust and does not model voltage sag, cell imbalance, temperature or protection.

At a given sample the calculations are:

```text
Power in watts = voltage in volts × current in amperes
Charge used in mAh = current in amperes × elapsed seconds × 1000 / 3600
Energy used in Wh = power in watts × elapsed seconds / 3600
Estimated charge remaining = maximum of zero and assumed starting capacity − charge used
```

The remaining value assumes the stated starting capacity and ideal counting. It is not a battery fuel gauge. A 3S capable charger must use the correct chemistry and balance settings for the specific pack. Do not connect the raw pack directly to the Raspberry Pi or low voltage sensors.

## Flight model

The vertical model calculates acceleration from thrust, mass, gravity and linear drag. It uses explicit Euler steps for altitude and velocity. This is a simplified model, not a measured aerodynamic model. There is no ground collision, propeller response or battery coupling.

The controller calculates an altitude error from the target and estimated altitude. It proposes an updated integral from the prior integral plus error multiplied by timestep. The unbounded thrust is the sum of gravity compensation, proportional correction and integral correction, less a velocity correction. The command is limited to the configured thrust range. The integral is held when saturation and the error would push the command farther beyond a limit.

The filter predicts altitude and velocity from synthetic acceleration. It updates them using synthetic pressure and scheduled altitude observations. The pressure model is an idealised exponential relationship. The filter uses the derivative of that relationship to update its covariance. Its innovation check compares the squared observation difference with the innovation variance. A rejected or missing observation is not treated as accepted data.

The dashboard shows the selected sample's controller terms and pressure innovation. The results section explains the calculation of tracking error, estimation error and their RMS values. The tests compare selected calculations with hand calculated results and numerical approximations. These checks are not formal proof of the model or evidence of physical flight safety.

## Candidate components for further engineering

These are examples to investigate. They are not claims about the original parts and they are not an approved bill of materials.

- A BMP390 pressure sensor is a candidate for barometric measurements. Bosch specifies the sensor supply range and I2C or SPI interfaces. Pressure readings still need placement and environmental assessment.
- An ICM 42688 P is a candidate motion sensor. TDK describes a three axis accelerometer and a three axis gyroscope. It does not provide absolute geographic position by itself.
- A u blox NEO M9N module is a candidate for outdoor GNSS position. A magnetometer such as the BMM350 may provide heading information, subject to calibration and interference. Neither provides obstacle detection.
- Raspberry Pi Camera Module 3 is a candidate for a camera interface. Raspberry Pi notes a possible interference risk with GPS frequencies. Camera placement, lens choice, timing and the vision task need separate evaluation.
- EMAX lists an E3 2306 2400 KV motor for three or four cell packs and five to five and a half inch propellers. That makes it a candidate for further sizing, not a verified match for this aircraft. Motor selection depends on measured aircraft mass, the exact propeller, thrust data, current draw, electronic speed controllers and cooling.
- Raspberry Pi documentation recommends a regulated 5.1 V supply and a 2.5 A supply for Raspberry Pi 3 models. The regulator and power distribution design must account for connected peripherals and transient loads.

No component is approved for a physical build by this simulation. Electrical protection, wiring, propeller selection, current limits, thermal behaviour and flight safety require a separate engineering review and appropriate testing.

## Sources

Gens Tattu battery reference: `https://www.genstattu.com/blog/how-to-choose-a-lipo-battery-for-rc`

Bosch BMP390: `https://www.bosch-sensortec.com/en/products/environmental-sensors/pressure-sensors/bmp390`

TDK ICM 42688 P: `https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p`

EMAX E3 2306: `https://shop.emax-usa.com/collections/new-products/products/e3-series-2306-brushless-motor-choose-kv`

Raspberry Pi power guidance: `https://www.raspberrypi.com/documentation/computers/raspberry-pi.html`

u blox NEO M9N: `https://www.u-blox.com/en/product/neo-m9n-module`

Bosch BMM350: `https://www.bosch-sensortec.com/en/products/motion-sensors/magnetometers`

Raspberry Pi Camera Module 3: `https://www.raspberrypi.com/documentation/accessories/camera-module-3.html`
