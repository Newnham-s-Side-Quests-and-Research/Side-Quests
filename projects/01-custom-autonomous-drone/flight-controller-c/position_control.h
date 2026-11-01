#ifndef DRONE_POSITION_CONTROL_H
#define DRONE_POSITION_CONTROL_H

/* This simulation component is not approved for aircraft control. */
#if defined(_WIN32)
#define DRONE_EXPORT __declspec(dllexport)
#else
#define DRONE_EXPORT
#endif

DRONE_EXPORT int drone_position_acceleration(const double target[3],
                                             const double position[3],
                                             const double velocity[3],
                                             const double proportional_gain[3],
                                             const double derivative_gain[3],
                                             double acceleration[3]);

#endif
