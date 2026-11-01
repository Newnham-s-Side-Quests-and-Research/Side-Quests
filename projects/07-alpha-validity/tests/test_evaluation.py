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
from alpha_validity.evaluation import EvaluationError,evaluate


def example():
    observations=[{'decision_time':i,'return_end_time':i+1,'return_bps':value} for i,value in enumerate((10,-5,20,-10))]
    candidates=[{'candidate_id':'long','signals':[{'available_at':i,'position':1} for i in range(4)]},
                {'candidate_id':'flat','signals':[{'available_at':i,'position':0} for i in range(4)]}]
    return {'schema_version':1,'cost_bps':2,'holdout_start':2,'observations':observations,'candidates':candidates}


class EvaluationTests(unittest.TestCase):
    def test_selection_and_holdout_are_hand_calculated(self):
        data=example();before=copy.deepcopy(data);result=evaluate(data)
        self.assertEqual(data,before)
        self.assertEqual(result['selected_candidate'],'long')
        self.assertEqual(result['development'][0]['sum_net_bps'],3)
        self.assertEqual(result['holdout']['sum_net_bps'],8)
        self.assertEqual(result['holdout']['turnover_units'],1)

    def test_holdout_results_do_not_change_selection(self):
        data=example();data['observations'][2]['return_bps']=-1000
        self.assertEqual(evaluate(data)['selected_candidate'],'long')

    def test_future_signal_and_overlapping_returns_fail(self):
        data=example();data['candidates'][0]['signals'][0]['available_at']=1
        with self.assertRaises(EvaluationError):evaluate(data)
        data=example();data['observations'][0]['return_end_time']=3
        with self.assertRaises(EvaluationError):evaluate(data)

    def test_duplicate_candidate_and_boolean_positions_fail(self):
        data=example();data['candidates'][1]['candidate_id']='long'
        with self.assertRaises(EvaluationError):evaluate(data)
        data=example();data['candidates'][0]['signals'][0]['position']=True
        with self.assertRaises(EvaluationError):evaluate(data)

    def test_command_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json';source.write_text(json.dumps(example()),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
            result=subprocess.run([sys.executable,'-m','alpha_validity',str(source)],cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['holdout']['sum_net_bps'],8)


if __name__=='__main__':unittest.main()
