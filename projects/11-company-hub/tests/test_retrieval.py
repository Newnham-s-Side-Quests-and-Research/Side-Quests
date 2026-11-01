import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from company_hub.retrieval import RetrievalError,SourceIndex


def sources():
    return [{'source_id':'public','version':'v1','text':'Café delivery due Monday.','roles':['staff']},
            {'source_id':'private','version':'v1','text':'Secret delivery due Tuesday.','roles':['finance']}]


class RetrievalTests(unittest.TestCase):
    def test_access_filter_is_applied_before_results(self):
        index=SourceIndex(sources())
        found=index.search('delivery',['staff'])
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['source_id'],'public')
        self.assertNotIn('Secret',json.dumps(found))
        self.assertEqual(index.search('Secret',['staff']),[])

    def test_resolution_rechecks_roles_and_digest(self):
        index=SourceIndex(sources());found=index.search('Café',['staff'])[0]
        reference={key:found[key] for key in ('source_id','version','sha256','start','end')}
        self.assertEqual(index.resolve(reference,['staff']),'Café')
        with self.assertRaises(RetrievalError):index.resolve(reference,[])
        reference['sha256']='0'*64
        with self.assertRaises(RetrievalError):index.resolve(reference,['staff'])

    def test_query_is_literal_and_positions_use_original_text(self):
        index=SourceIndex(sources())
        self.assertEqual(index.search('.*',['staff']),[])
        row=index.search('DELIVERY',['staff'])[0]
        self.assertEqual(row['text'],'delivery')
        self.assertEqual(row['start'],5)

    def test_invalid_sources_and_duplicate_versions_fail(self):
        with self.assertRaises(RetrievalError):SourceIndex(sources()+[sources()[0]])
        bad=sources();bad[0]['roles']=[]
        with self.assertRaises(RetrievalError):SourceIndex(bad)

    def test_command_returns_only_authorised_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json'
            source.write_text(json.dumps({'sources':sources(),'roles':['staff'],'query':'delivery'}),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
            result=subprocess.run([sys.executable,'-m','company_hub',str(source)],cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual([row['source_id'] for row in json.loads(result.stdout)['matches']],['public'])
            self.assertNotIn('private',result.stdout)


if __name__=='__main__':unittest.main()
