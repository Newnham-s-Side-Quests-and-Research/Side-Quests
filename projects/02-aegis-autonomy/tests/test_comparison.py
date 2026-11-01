import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from aegis_autonomy.comparison import compare
from aegis_autonomy.monitor import MonitoringError


def example():
    return {'schema_version':1,'supervisor':{'alarms_to_degrade':1,'clears_to_recover':1,'max_gap_seconds':2},
            'monitors':[{'monitor_id':'sensitive','method':'absolute','threshold':2},
                        {'monitor_id':'strict','method':'absolute','threshold':10}],
            'observations':[{'timestamp_s':0,'residual':3,'variance':1,'label':'healthy'},
                            {'timestamp_s':1,'residual':1,'variance':1,'label':'healthy'},
                            {'timestamp_s':2,'residual':1,'variance':1,'label':'fault'},
                            {'timestamp_s':3,'residual':4,'variance':1,'label':'fault'},
                            {'timestamp_s':4,'residual':None,'variance':None,'label':'unknown'},
                            {'timestamp_s':5,'residual':1,'variance':1,'label':'fault'}]}


class ComparisonTests(unittest.TestCase):
    def test_false_alarm_fraction_and_fault_windows(self):
        data=example();before=copy.deepcopy(data);report=compare(data)
        self.assertEqual(data,before)
        first,second=report['results']
        self.assertEqual((first['healthy_alarm_samples'],first['healthy_samples']), (1,2))
        self.assertEqual(first['healthy_alarm_fraction'],0.5)
        self.assertEqual(first['fault_windows'][0]['detection_delay_s'],1)
        self.assertFalse(first['fault_windows'][1]['detected'])
        self.assertIsNone(first['fault_windows'][1]['detection_delay_s'])
        self.assertFalse(second['fault_windows'][0]['detected'])
        self.assertEqual([r['observation'] for r in first['trace']], [r['observation'] for r in second['trace']])

    def test_zero_healthy_samples_and_duplicate_monitors(self):
        data=example()
        for row in data['observations']:row['label']='fault'
        self.assertIsNone(compare(data)['results'][0]['healthy_alarm_fraction'])
        data['monitors'][1]['monitor_id']='sensitive'
        with self.assertRaises(MonitoringError):compare(data)

    def test_missing_healthy_observation_is_not_counted_as_clear(self):
        data=example();data['observations'][1]['residual']=None
        result=compare(data)['results'][0]
        self.assertEqual(result['healthy_samples'],2)
        self.assertEqual(result['healthy_observed_samples'],1)
        self.assertEqual(result['healthy_unavailable_samples'],1)
        self.assertEqual(result['healthy_alarm_fraction'],1.0)

    def test_command_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json';source.write_text(json.dumps(example()),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
            result=subprocess.run([sys.executable,'-m','aegis_autonomy.compare',str(source)],cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['results'][0]['healthy_alarm_fraction'],0.5)


if __name__=='__main__':unittest.main()
