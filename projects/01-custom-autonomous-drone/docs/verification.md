# Verification record

The current checks run locally with synthetic data. The latest suite contains 42 tests. All passed in the project folder and in a clean temporary copy without network access. It covers register validation, duplicate records, unknown references, hash changes, missing files, path escapes and rights states.

The signal tests cover a hand calculated motion step, repeatability with a fixed seed, altitude bias, missing altitude samples, output bounds and invalid configuration. They also check a free fall example, integral holding, ideal pressure conversion, ideal motion readings and simulated link outages.

The vertical estimator is checked against hand calculated prediction and observation updates. Its pressure derivative is compared with a numerical approximation. The tests cover rejected outliers, invalid inputs, covariance checks and a deterministic synthetic replay with missing position samples.

The grid planner is compared with an independent breadth first search over all 128 obstacle arrangements in a small grid. The image detector is checked against synthetic pixels with known regions and noise. The telemetry checks preserve missing signals and label unmodelled hardware as unknown.

The integration checks run the components on the same synthetic scenario. The clean copy produced 50 signal steps, 50 estimates, 50 telemetry snapshots, a route of 12 grid steps and one synthetic image region. The report retains the input configuration and reports a missing route or image detection explicitly. They do not establish a closed flight control loop.

These checks establish behaviour for the cases tested. They do not prove all possible inputs, real sensor behaviour, wireless communication, stability in flight or the behaviour of the missing original controller. Independent engineering review remains outstanding.
