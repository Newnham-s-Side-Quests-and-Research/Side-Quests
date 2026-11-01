import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OrderBookCompilationTests(unittest.TestCase):
    def test_compile_and_run_native_cases(self):
        zig = os.environ.get('DRONE_ZIG')
        compiler = [zig, 'c++'] if zig else ([shutil.which('c++')] if shutil.which('c++') else None)
        if compiler is None:
            self.skipTest('A C++17 compiler is required')
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / ('book-test.exe' if os.name == 'nt' else 'book-test')
            args = compiler + ['-std=c++17', str(ROOT / 'src' / 'order_book.cpp'),
                               str(ROOT / 'tests' / 'order_book_test.cpp'), '-o', str(output)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr[-5000:])
            result = subprocess.run([str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
