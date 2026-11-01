"""Load the optional native position controller into the synthetic simulator."""
import ctypes
from .simulation import SimulationError


def load_position_controller(path):
    library = ctypes.CDLL(str(path))
    vector = ctypes.c_double * 3
    function = library.drone_position_acceleration
    function.argtypes = [ctypes.POINTER(ctypes.c_double)] * 6
    function.restype = ctypes.c_int

    def calculate(target, position, velocity, proportional_gain, derivative_gain):
        arrays = [vector(*values) for values in (target, position, velocity, proportional_gain, derivative_gain)]
        output = vector()
        if function(*arrays, output) != 0:
            raise SimulationError('Native position controller rejected its inputs')
        return list(output)

    return calculate
