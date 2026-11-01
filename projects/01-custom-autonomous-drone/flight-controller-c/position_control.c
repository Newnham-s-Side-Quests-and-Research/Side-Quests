#include "position_control.h"
#include <math.h>
#include <stddef.h>

int drone_position_acceleration(const double target[3], const double position[3],
                                const double velocity[3], const double proportional_gain[3],
                                const double derivative_gain[3], double acceleration[3])
{
    double result[3];
    size_t i;
    if (!target || !position || !velocity || !proportional_gain || !derivative_gain || !acceleration) {
        return 1;
    }
    for (i = 0; i < 3; ++i) {
        if (!isfinite(target[i]) || !isfinite(position[i]) || !isfinite(velocity[i]) ||
            !isfinite(proportional_gain[i]) || !isfinite(derivative_gain[i]) ||
            proportional_gain[i] < 0 || derivative_gain[i] < 0) {
            return 1;
        }
        result[i] = proportional_gain[i] * (target[i] - position[i]) - derivative_gain[i] * velocity[i];
        if (!isfinite(result[i])) {
            return 1;
        }
    }
    for (i = 0; i < 3; ++i) {
        acceleration[i] = result[i];
    }
    return 0;
}
