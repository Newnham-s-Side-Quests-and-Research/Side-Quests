import sys
import os
import json
import subprocess
import tempfile
from collections import deque
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.planning import PlanningError, plan_grid

class PlanningTests(unittest.TestCase):
    def test_route_uses_only_clear_neighbouring_cells(self):
        blocked = {(2,0), (2,1), (2,2), (2,3)}
        route = plan_grid(5, 5, blocked, (0,0), (4,0))
        self.assertEqual(route[0], (0,0)); self.assertEqual(route[-1], (4,0))
        self.assertTrue(all(p not in blocked for p in route))
        self.assertTrue(all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1 for a,b in zip(route,route[1:])))
        self.assertEqual(len(route)-1, 12)
        self.assertEqual(route, plan_grid(5,5,blocked,(0,0),(4,0)))

    def test_no_route_and_same_start_goal(self):
        self.assertIsNone(plan_grid(3,3,{(1,0),(1,1),(1,2)},(0,1),(2,1)))
        self.assertEqual(plan_grid(2,2,[],(1,1),(1,1)), [(1,1)])

    def test_bad_inputs_are_rejected(self):
        cases = [(0,2,[],(0,0),(1,1)), (2,2,[(2,0)],(0,0),(1,1)),
                 (2,2,[(0,0)],(0,0),(1,1)), (2,2,[],(-1,0),(1,1)),
                 (2,2,[],(True,0),(1,1)), (1001,1000,[],(0,0),(1,1))]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(PlanningError):plan_grid(*case)

    def test_cli_writes_a_route_and_reports_no_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'route.json'
            scenario = ROOT / 'fixtures' / 'grid-scenario.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'plan', str(scenario), '--output', str(output)], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(output.read_text(encoding='utf-8'))['route']) - 1, 12)
            data = json.loads(scenario.read_text(encoding='utf-8'))
            data['blocked'].append([2,4])
            blocked = Path(tmp) / 'blocked.json'; blocked.write_text(json.dumps(data), encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'plan', str(blocked), '--output', str(output)], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIsNone(json.loads(output.read_text(encoding='utf-8'))['route'])

    def test_exhaustive_small_grids_against_breadth_first_search(self):
        width = height = 3; start = (0,0); goal = (2,2)
        cells = [(x,y) for y in range(height) for x in range(width) if (x,y) not in (start,goal)]
        for mask in range(1 << len(cells)):
            blocked = {p for i,p in enumerate(cells) if mask & (1 << i)}
            queue = deque([(start,0)]); visited = {start}; expected = None
            while queue:
                point, distance = queue.popleft()
                if point == goal: expected = distance; break
                for dx,dy in ((0,-1),(-1,0),(1,0),(0,1)):
                    nxt=(point[0]+dx,point[1]+dy)
                    if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in blocked and nxt not in visited:
                        visited.add(nxt);queue.append((nxt,distance+1))
            route = plan_grid(width,height,blocked,start,goal)
            self.assertEqual(None if route is None else len(route)-1, expected, f'mask {mask}')

if __name__ == '__main__': unittest.main()
