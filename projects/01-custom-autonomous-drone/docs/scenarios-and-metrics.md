# Synthetic scenarios and metrics

The local dashboard runs four reproducible versions of the vertical model. They all use the same base configuration and seed. Existing fault settings in a supplied configuration are cleared before each dashboard scenario applies its own fault. The complete effective configuration is included in the downloaded run data.

## Scenarios

- Normal signals use the configured synthetic noise without an injected fault.
- Position observations lost removes both pressure and GPS altitude readings during the selected interval.
- Motion signal lost removes the simulated motion input during the selected interval.
- Pressure reading biased adds a large offset to the pressure reading while GPS altitude readings continue.

For the supplied 300 sample fixture, the fault interval starts at zero based step 100 and ends before step 130. The dashboard presents this as samples 101 to 130. The fault windows are part of the test setup rather than observations from a real flight.

## Measures

Tracking error is simulated altitude minus the target altitude. Estimation error is estimated altitude minus simulated altitude. RMS is the square root of the mean squared error across the recorded samples. Largest tracking error is the largest absolute tracking error across those samples. The final state occurs after the last recorded sample and is included in the downloadable report.

Pressure counts cover each recorded sample. GPS counts cover only scheduled GPS samples. Accepted and rejected observations refer to the filter innovation check. Missing motion samples and degraded samples are counted over the full trace. Maximum thrust is the largest command in the synthetic trace.

Each downloaded report includes the scenario description, effective configuration, seed, metrics, individual samples and stated limitations. These values show the behaviour of this model under the chosen conditions. They do not establish real aircraft performance or safety.

## Boundaries

The model has no ground contact, aircraft attitude, motors, battery, camera or real geographic coordinates. During a degraded state it uses zero thrust as a test convention. That convention is not a safe flight procedure. The dashboard is a local read only tool with no login, real radio connection or hardware control.

## Three cell power example

Each scenario includes the same separate electrical example. It assumes three standard LiPo cells in series, 1500 mAh of starting capacity, a fixed nominal voltage of 11.1 V and a fixed current of 8 A. These are illustrative inputs. They are not measurements of the original battery or motor current.

Power equals voltage multiplied by current. Charge used equals current multiplied by elapsed seconds and by 1000, then divided by 3600. Energy used equals power multiplied by elapsed seconds, then divided by 3600. The displayed remaining charge starts from the assumed capacity and is limited to zero. The fixed nominal voltage does not indicate actual charge level.

This calculation does not change the flight model. It does not represent motor loads, cell imbalance, voltage sag, temperature or protection. The full charge reference is 12.6 V for three standard cells at 4.2 V each. The actual pack and its safe operating limits require manufacturer data and physical review.
