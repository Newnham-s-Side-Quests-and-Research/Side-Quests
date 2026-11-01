import copy
from collections import deque
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.mission3d import MissionError, plan_voxels, run_mission

class VoxelPlannerTests(unittest.TestCase):
    def test_exhaustive_small_grids_against_breadth_first_search(self):
        size=(2,2,2); start=(0,0,0); goal=(1,1,1)
        cells=[(x,y,z) for x in range(2) for y in range(2) for z in range(2) if (x,y,z) not in (start,goal)]
        for mask in range(1 << len(cells)):
            blocked={point for i,point in enumerate(cells) if mask & (1 << i)}
            queue=deque([(start,0)]);visited={start};expected=None
            while queue:
                point,distance=queue.popleft()
                if point == goal:
                    expected=distance;break
                for delta in ((-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)):
                    nxt=tuple(point[i]+delta[i] for i in range(3))
                    if all(0 <= nxt[i] < size[i] for i in range(3)) and nxt not in blocked and nxt not in visited:
                        visited.add(nxt);queue.append((nxt,distance+1))
            route=plan_voxels(size,blocked,start,goal)
            self.assertEqual(None if route is None else len(route)-1,expected,f'mask {mask}')
            if route:
                self.assertTrue(all(point not in blocked for point in route))
                self.assertTrue(all(sum(abs(a[i]-b[i]) for i in range(3)) == 1 for a,b in zip(route,route[1:])))

    def test_invalid_inputs_and_blocked_endpoint(self):
        cases=[((0,2,2),[],(0,0,0),(1,1,1)),((2,2,2),[],(True,0,0),(1,1,1)),
               ((2,2,2),[(0,0,0)],(0,0,0),(1,1,1)),((2,2,2),[(2,0,0)],(0,0,0),(1,1,1)),
               ((1000,1000,1000),[],(0,0,0),(1,1,1))]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(MissionError):plan_voxels(*args)

class MissionTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'fixtures'/'mission3d-scenario.json').read_text(encoding='utf-8'))

    def test_route_reaches_goal_and_pauses_on_position_loss(self):
        original=copy.deepcopy(self.config);result=run_mission(self.config)
        self.assertEqual(self.config,original)
        self.assertEqual(result,run_mission(self.config))
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['final_position_m'],(3.0,0.0,0.0))
        self.assertEqual(result['distance_m'],7.0)
        self.assertEqual(len(result['trace']),32)
        for row in result['trace']:
            actual=math.dist(row['position_before_m'],row['position_after_m'])
            self.assertAlmostEqual(actual,row['distance_m'])
            self.assertLessEqual(actual, self.config['speed_m_s'] * self.config['dt_seconds'])
            if 3 <= row['step'] < 7:
                self.assertEqual(row['state'],'position unavailable')
                self.assertEqual(row['position_before_m'],row['position_after_m'])
        self.assertIn('No attitude, motor, wind, battery or three dimensional flight dynamics',result['limitations'])

    def test_no_route_and_incomplete_are_explicit(self):
        config=copy.deepcopy(self.config)
        config['grid']['blocked']=[[1,y,z] for y in range(3) for z in range(3)]
        result=run_mission(config)
        self.assertEqual(result['status'],'no route');self.assertEqual(result['trace'],[])
        config=copy.deepcopy(self.config);config['max_steps']=2;config['position_dropout']=None
        self.assertEqual(run_mission(config)['status'],'incomplete')

    def test_invalid_time_speed_and_dropout(self):
        for key,value in [('dt_seconds',0),('speed_m_s',-1),('max_steps',True),('cell_size_m',float('inf')),
                          ('position_dropout',{'start':5,'end':3})]:
            with self.subTest(key=key), self.assertRaises(MissionError):run_mission(dict(self.config,**{key:value}))

    def test_command_writes_labelled_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');output=Path(tmp)/'mission.json'
            result=subprocess.run([sys.executable,'-m','drone_archive','mission3d',str(ROOT/'fixtures'/'mission3d-scenario.json'),'--output',str(output)],cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['status'],'complete')
            self.assertIn('No camera perception or physical aircraft has been verified',report['limitations'])

if __name__ == '__main__': unittest.main()
