"""Select on development observations and evaluate an untouched holdout."""
import re


class EvaluationError(ValueError):
    pass


def _id(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value,re.ASCII):
        raise EvaluationError('Invalid candidate ID')
    return value


def _integer(value,name,minimum,maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise EvaluationError(f'Invalid {name}')
    return value


def evaluate(data):
    if not isinstance(data,dict) or set(data) != {'schema_version','cost_bps','holdout_start','observations','candidates'}:
        raise EvaluationError('Invalid evaluation fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise EvaluationError('Unsupported schema version')
    cost=_integer(data['cost_bps'],'cost',0,10000)
    observations=data['observations'];candidates=data['candidates']
    if not isinstance(observations,list) or not 2 <= len(observations) <= 100000:
        raise EvaluationError('Observations must be a bounded list')
    split=_integer(data['holdout_start'],'holdout start',1,len(observations)-1)
    if not isinstance(candidates,list) or not 1 <= len(candidates) <= 1000:
        raise EvaluationError('Candidates must be a bounded list')
    previous_end=None
    for item in observations:
        if not isinstance(item,dict) or set(item) != {'decision_time','return_end_time','return_bps'}:
            raise EvaluationError('Invalid observation')
        start=_integer(item['decision_time'],'decision time',0,2**53-1)
        end=_integer(item['return_end_time'],'return end time',0,2**53-1)
        _integer(item['return_bps'],'return',-1_000_000,1_000_000)
        if end <= start or (previous_end is not None and start < previous_end):
            raise EvaluationError('Return intervals must be ordered and nonoverlapping')
        previous_end=end
    ids=set();scored=[]
    def score(items,signals):
        previous=0;total=0;turnover=0
        for observation,signal in zip(items,signals):
            change=abs(signal['position']-previous)
            total+=signal['position']*observation['return_bps']-change*cost
            turnover+=change;previous=signal['position']
        return {'sum_net_bps':total,'turnover_units':turnover,'periods':len(items)}
    for candidate in candidates:
        if not isinstance(candidate,dict) or set(candidate) != {'candidate_id','signals'}:
            raise EvaluationError('Invalid candidate')
        candidate_id=_id(candidate['candidate_id'])
        if candidate_id in ids: raise EvaluationError('Duplicate candidate ID')
        ids.add(candidate_id);signals=candidate['signals']
        if not isinstance(signals,list) or len(signals)!=len(observations):
            raise EvaluationError('Each candidate needs one signal per observation')
        for signal,observation in zip(signals,observations):
            if not isinstance(signal,dict) or set(signal) != {'available_at','position'}:
                raise EvaluationError('Invalid signal')
            available=_integer(signal['available_at'],'signal availability',0,2**53-1)
            if available > observation['decision_time']:
                raise EvaluationError('Signal is not available at decision time')
            _integer(signal['position'],'position',-1,1)
        scored.append({'candidate_id':candidate_id,'development':score(observations[:split],signals[:split]),'signals':signals})
    selected=min(scored,key=lambda item:(-item['development']['sum_net_bps'],item['candidate_id']))
    holdout=score(observations[split:],selected['signals'][split:])
    return {'schema_version':1,'selected_candidate':selected['candidate_id'],
            'development':[{'candidate_id':item['candidate_id'],**item['development']} for item in scored],
            'holdout':holdout,'cost_bps':cost,
            'limitations':['Results depend on supplied observations and availability timestamps',
                           'Period returns are summed without compounding and each window begins flat without a closing trade',
                           'No slippage, leverage, market impact or financing costs are modelled',
                           'This does not establish a tradable strategy or provide investment advice']}
