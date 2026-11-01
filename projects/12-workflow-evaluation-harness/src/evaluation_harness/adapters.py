"""Deterministic adapters used to exercise the harness offline."""
from copy import deepcopy

class FixtureAdapter:
    def __init__(self, mode):
        if mode not in ('sound', 'wrong_field', 'false_accept', 'false_abstain'):
            raise ValueError('Unknown fixture adapter')
        self.mode = mode
        self.version = f'fixture:{mode}:1'

    def run(self, value, settings):
        fields = deepcopy(value['fields'])
        abstain = value['abstain']
        if self.mode == 'wrong_field' and not abstain:
            fields['amount'] = -1
        elif self.mode == 'false_accept' and abstain:
            abstain = False
        elif self.mode == 'false_abstain' and not abstain:
            abstain = True
        return {'fields': fields, 'abstain': abstain}
