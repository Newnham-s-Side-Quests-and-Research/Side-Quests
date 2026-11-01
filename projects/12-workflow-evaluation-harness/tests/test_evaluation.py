import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation_harness.cases import CaseError, load_cases
from evaluation_harness.gates import evaluate
from evaluation_harness.runner import compare

CASE_DATA = {'schema_version': 1, 'cases': [{'id': 'invoice-1', 'category': 'normal', 'split': 'test', 'rights': 'synthetic', 'input': {'fields': {'amount': 100, 'supplier': 'Oak'}, 'abstain': False}, 'expected': {'fields': {'amount': 100, 'supplier': 'Oak'}, 'abstain': False}}, {'id': 'invoice-2', 'category': 'normal', 'split': 'test', 'rights': 'synthetic', 'input': {'fields': {'amount': 250, 'supplier': 'Ash'}, 'abstain': False}, 'expected': {'fields': {'amount': 250, 'supplier': 'Ash'}, 'abstain': False}}, {'id': 'uncertain-1', 'category': 'uncertain', 'split': 'test', 'rights': 'synthetic', 'input': {'fields': {}, 'abstain': True}, 'expected': {'fields': {}, 'abstain': True}}]}

class ExampleAdapter:
    def __init__(self, mode):
        self.mode = mode

    def run(self, value, settings):
        fields = copy.deepcopy(value['fields'])
        abstain = value['abstain']
        if self.mode == 'wrong_field' and not abstain:
            fields['amount'] = -1
        elif self.mode == 'false_accept' and abstain:
            abstain = False
        elif self.mode == 'false_abstain' and not abstain:
            abstain = True
        return {'fields': fields, 'abstain': abstain}


class SoundAdapter(ExampleAdapter):
    version = 'sound'
    def __init__(self): super().__init__('sound')

class WrongFieldAdapter(ExampleAdapter):
    version = 'wrong'
    def __init__(self): super().__init__('wrong_field')

class FalseAcceptAdapter(ExampleAdapter):
    version = 'false_accept'
    def __init__(self): super().__init__('false_accept')

class FalseAbstainAdapter(ExampleAdapter):
    version = 'false_abstain'
    def __init__(self): super().__init__('false_abstain')


RULES = {'version': 1, 'minimum_cases': 3, 'minimum_field_delta': 0.0, 'minimum_abstention_accuracy': 1.0}

class EvaluationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.case_file = Path(directory.name) / 'cases.json'
        self.case_file.write_text(json.dumps(CASE_DATA), encoding='utf-8')
        self.data, self.digest = load_cases(self.case_file)
        self.cases = self.data['cases']

    def test_known_scores_and_planted_defects(self):
        for candidate, expected in [('sound','pass'),('wrong_field','fail'),('false_accept','fail'),('false_abstain','fail')]:
            with self.subTest(candidate=candidate):
                result = compare(self.cases, ExampleAdapter('sound'), ExampleAdapter(candidate), {})
                self.assertEqual(evaluate(result, RULES)['status'], expected)
        result = compare(self.cases, ExampleAdapter('sound'), ExampleAdapter('wrong_field'), {})
        self.assertEqual((result['candidate']['field_correct'], result['candidate']['field_total']), (2,4))
        self.assertEqual(result['candidate']['abstention_correct'], 3)

    def test_boolean_does_not_equal_integer_field(self):
        cases = copy.deepcopy(self.cases)
        cases[0]['expected']['fields']['amount'] = True
        scores = compare(cases, ExampleAdapter('sound'), ExampleAdapter('sound'), {})
        self.assertFalse(scores['candidate']['details'][0]['field_checks'][0]['correct'])

    def test_inputs_are_same_and_independent(self):
        class RecordingAdapter:
            def __init__(self): self.inputs=[]
            def run(self, value, settings):
                self.inputs.append(copy.deepcopy(value)); value['fields']['injected'] = True
                return {'fields': value['fields'], 'abstain': value['abstain']}
        a,b=RecordingAdapter(),RecordingAdapter(); original=copy.deepcopy(self.cases)
        compare(self.cases,a,b,{})
        self.assertEqual(a.inputs,b.inputs); self.assertEqual(self.cases,original)

    def test_failures_and_missing_metrics_are_incomplete(self):
        class Broken:
            def run(self, value, settings): raise RuntimeError('Unavailable')
        result=compare(self.cases,ExampleAdapter('sound'),Broken(),{})
        self.assertEqual(result['candidate']['errors'],3)
        self.assertEqual(result['candidate']['details'][0]['result']['error']['type'],'RuntimeError')
        self.assertEqual(evaluate(result,RULES)['status'],'incomplete')
        only_abstain=[self.cases[-1]]*3
        self.assertEqual(evaluate(compare(only_abstain,ExampleAdapter('sound'),ExampleAdapter('sound'),{}),RULES)['status'],'incomplete')
        self.assertEqual(evaluate(compare(self.cases[:1],ExampleAdapter('sound'),ExampleAdapter('sound'),{}),RULES)['status'],'incomplete')

    def test_invalid_cases_rejected_and_hash_is_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'cases.json'
            for mutation in ('duplicate','version','missing'):
                data=copy.deepcopy(self.data)
                if mutation=='duplicate': data['cases'][1]['id']=data['cases'][0]['id']
                if mutation=='version': data['schema_version']=2
                if mutation=='missing': del data['cases'][0]['expected']
                file.write_text(json.dumps(data),encoding='utf-8')
                with self.subTest(mutation=mutation), self.assertRaises(CaseError):load_cases(file)
            file.write_text(json.dumps(self.data,indent=4),encoding='utf-8')
            self.assertEqual(load_cases(file)[1],self.digest)

    def test_cli_end_to_end_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join((str(ROOT/'src'), str(Path(__file__).parent)))
            for candidate, code in [('sound',0),('wrong_field',1),('false_accept',1),('false_abstain',1)]:
                out=Path(tmp)/candidate
                proc=subprocess.run([sys.executable,'-m','evaluation_harness','--cases',str(self.case_file),'--baseline','test_evaluation:SoundAdapter','--candidate', {'sound':'test_evaluation:SoundAdapter','wrong_field':'test_evaluation:WrongFieldAdapter','false_accept':'test_evaluation:FalseAcceptAdapter','false_abstain':'test_evaluation:FalseAbstainAdapter'}[candidate],'--output',str(out)],cwd=ROOT,env=env,capture_output=True,text=True)
                self.assertEqual(proc.returncode,code,proc.stderr)
                report=json.loads((out/'report.json').read_text(encoding='utf-8'))
                self.assertEqual(report['case_set_sha256'],self.digest)
                self.assertEqual(len(report['scores']['candidate']['details']),3)
                self.assertIn('person',report['release_decision'])
                self.assertTrue((out/'report.txt').is_file())
            bad=subprocess.run([sys.executable,'-m','evaluation_harness','--cases',str(Path(tmp)/'missing.json'),'--baseline','test_evaluation:SoundAdapter','--candidate','test_evaluation:SoundAdapter','--output',str(Path(tmp)/'invalid')],cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(bad.returncode,3)

if __name__=='__main__': unittest.main()
