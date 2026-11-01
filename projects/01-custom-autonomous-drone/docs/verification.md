# Verification record

The current checks run locally with synthetic data. They cover register validation, duplicate records, unknown references, hash changes, missing files, path escapes and rights states.

The signal tests cover a hand calculated motion step, repeatability with a fixed seed, altitude bias, missing altitude samples, output bounds and invalid configuration. They also check a free fall example, integral holding, ideal pressure conversion, ideal IMU readings and independent simulated link outages.

The command line test writes a 50 step synthetic trace from a temporary working directory. The trace labels the model and its limits. All 16 tests passed in the project folder and in a clean temporary copy. The scenario produced 50 steps with three missing altitude samples, three simulated WiFi outage steps and two simulated Bluetooth outage steps.

These checks establish behaviour for the cases tested. They do not prove all possible inputs, real sensor behaviour, wireless communication, stability in flight or the behaviour of the missing original controller. Independent engineering review remains outstanding.
