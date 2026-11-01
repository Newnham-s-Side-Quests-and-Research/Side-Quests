from test_inputs import input_path
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.flight3d import run_controlled_flight


@unittest.skipUnless(os.environ.get('DRONE_ZIG'), 'Set DRONE_ZIG to the Zig executable to build the C tests')
class NativeControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.library_path = Path(cls.temp.name) / ('controller.dll' if os.name == 'nt' else 'controller.so')
        source = ROOT / 'flight-controller-c' / 'position_control.c'
        command = [os.environ['DRONE_ZIG'], 'cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                   '-shared', str(source), '-o', str(cls.library_path)]
        subprocess.run(command, check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_known_result_and_invalid_values(self):
        script = '''
import math, sys
from drone_archive.c_controller import load_position_controller
from drone_archive.simulation import SimulationError
calculate = load_position_controller(sys.argv[1])
assert calculate([2,-1,3],[1,1,2],[0.5,-0.5,0],[2,3,1],[1,2,4]) == [1.5,-5,1]
for target, gain in (([math.nan,0,0],[1]*3), ([0]*3,[-1,1,1])):
    try:
        calculate(target,[0]*3,[0]*3,gain,[1]*3)
    except SimulationError:
        continue
    raise AssertionError('Invalid values were accepted')
'''
        self.run_child(script)

    def run_child(self, script):
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT / 'src')
        result = subprocess.run([sys.executable, '-c', script, str(self.library_path)], env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_native_and_python_integrated_flights_agree(self):
        config = json.loads((input_path('controlled-flight-scenario.json')).read_text(encoding='utf-8'))
        python_report = run_controlled_flight(config)
        script = '''
import json, sys
from drone_archive.c_controller import load_position_controller
from drone_archive.flight3d import run_controlled_flight
with open(sys.argv[2], encoding='utf-8') as source:
    config = json.load(source)
print(json.dumps(run_controlled_flight(config, position_controller=load_position_controller(sys.argv[1]))))
'''
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT / 'src')
        result = subprocess.run([sys.executable, '-c', script, str(self.library_path),
                                 str(input_path('controlled-flight-scenario.json'))],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        native_report = json.loads(result.stdout)
        self.assertEqual(len(python_report['trace']), len(native_report['trace']))
        for python_row, native_row in zip(python_report['trace'], native_report['trace']):
            for first, second in zip(python_row['position_m'], native_row['position_m']):
                self.assertAlmostEqual(first, second, places=10)
            for first, second in zip(python_row['motor_command_n'], native_row['motor_command_n']):
                self.assertAlmostEqual(first, second, places=10)

    def test_null_pointer_is_rejected_without_writing_output(self):
        script = '''
import ctypes, sys
library = ctypes.CDLL(sys.argv[1])
function = library.drone_position_acceleration
function.argtypes = [ctypes.POINTER(ctypes.c_double)] * 6
function.restype = ctypes.c_int
vector = ctypes.c_double * 3
valid = vector(1, 1, 1)
output = vector(9, 9, 9)
assert function(None, valid, valid, valid, valid, output) != 0
assert list(output) == [9, 9, 9]
'''
        self.run_child(script)


if __name__ == '__main__':
    unittest.main()
