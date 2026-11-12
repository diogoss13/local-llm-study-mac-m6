#!/usr/bin/env python3
"""Adapted macOS runner, including the post-session early-prefill monitor fix."""
import argparse,os,json,time,urllib.request,pathlib,subprocess,re,random,threading,socket,hashlib
parser=argparse.ArgumentParser(description="Run synthetic long-context retrieval on macOS; preserve the original Portuguese questions.")
parser.add_argument('--base-url',default='http://127.0.0.1:11434')
parser.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path('outputs/context'))
parser.add_argument('--models',help='Comma-separated installed study model tags')
parser.add_argument('--levels',help='Comma-separated context sizes in tokens')
parser.add_argument('--timeout',type=int,default=900,help='Per-call timeout in seconds; use 1800 for the largest run')
ARGS=parser.parse_args()
if ARGS.timeout<=0:parser.error('--timeout must be positive')
OUT=ARGS.output_dir;OUT.mkdir(parents=True,exist_ok=True)
BASE=ARGS.base_url.rstrip('/')
if ARGS.models:os.environ['CONTEXT_MODELS']=ARGS.models
if ARGS.levels:os.environ['CONTEXT_LEVELS']=ARGS.levels
RESULTS=[]
OUTPUT='results.json'
MODELS=[('qwen3.5:9b-q4_K_M',262144),('gemma4:12b',262144),('qwen2.5-coder:14b',32768),('deepseek-coder-v2:16b',163840)]
def memory():
 def command(*args):return subprocess.check_output(args,text=True).strip()
 s=command('sysctl','-n','vm.swapusage');m=re.search(r'used = ([0-9.]+)M',s)
 return {'swap_used_mb':float(m.group(1)) if m else None,'pressure':int(command('sysctl','-n','kern.memorystatus_vm_pressure_level'))}
def save():
 (OUT/OUTPUT).write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
def emit(s):print(s if isinstance(s,str) else json.dumps(s,ensure_ascii=False),flush=True)
def req(path,data=None,timeout=900,guard=False):
 if not guard:
  request=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=timeout) as response:return json.load(response)
 import http.client
 data=dict(data,stream=True)
 from urllib.parse import urlsplit
 url=urlsplit(BASE)
 if url.scheme!='http' or url.path not in ('','/'):raise ValueError('Use an HTTP Ollama base URL without a path prefix')
 connection=http.client.HTTPConnection(url.hostname,url.port or 80,timeout=timeout)
 connection.request('POST',path,body=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 stop=threading.Event();samples=[];aborted=[];start=time.monotonic();baseline=memory()['swap_used_mb']
 def watch():
  count=0
  while not stop.wait(3):
   try:
    mem=memory();samples.append(mem)
    danger=mem['pressure']>=4 or mem['swap_used_mb']-baseline>2048
    count=count+1 if danger else 0
    if count>=3 or time.monotonic()-start>timeout:
     aborted.append('memory pressure/swap growth' if count>=3 else 'time limit')
     emit({'interruption':aborted[-1],'memory':mem})
     connection.sock.shutdown(socket.SHUT_RDWR)
     return
   except Exception:return
 thread=threading.Thread(target=watch,daemon=True);thread.start()
 message={'role':'assistant','content':''};final={}
 try:
  # Monitor the open socket before response headers or tokens arrive.
  response=connection.getresponse()
  if response.status>=400:raise RuntimeError(response.read().decode())
  for line in response:
   part=json.loads(line)
   if 'error' in part:raise RuntimeError(part['error'])
   msg=part.get('message',{});message['content']+=msg.get('content','')
   if msg.get('thinking'):message['thinking']=message.get('thinking','')+msg['thinking']
   if part.get('done'):final=part
  if aborted:raise RuntimeError('Test interrupted: '+aborted[0])
  if not final:raise RuntimeError('Incomplete response')
  final['message']=message;final['memory_samples']=samples
  return final
 except Exception:
  if aborted:raise RuntimeError('Test interrupted: '+aborted[0])
  raise
 finally:
  stop.set();thread.join(timeout=1);connection.close()

def call(model,ctx,prompt,think,max_tokens=128):
 data={'model':model,'messages':[{'role':'user','content':prompt}],'keep_alive':'15m','options':{'num_ctx':ctx,'num_predict':max_tokens,'temperature':0}}
 if think:data['think']=False
 start=time.monotonic();r=req('/api/chat',data,guard=True,timeout=ARGS.timeout)
 return {'seconds':round(time.monotonic()-start,3),'tokens_per_second':round(r.get('eval_count',0)*1e9/r['eval_duration'],2) if r.get('eval_duration') else None,'prompt_tokens':r.get('prompt_eval_count'),'prompt_eval_seconds':round(r.get('prompt_eval_duration',0)/1e9,3),'response':r}

def document(n):
 rng=random.Random(20261111)
 lines=[f'Record {i:06d}: Project archive describes routine maintenance, document review, scheduled backups and verification of completed tasks. Reference {rng.randrange(10000,99999)}.\n' for i in range(n)]
 secrets={}
 for label,fraction in [('BEGIN',.03),('MIDDLE',.50),('END',.97)]:
  for j in range(2):
   key=label+str(j+1);value=''.join(rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(10));index=min(n-1,int(n*fraction)+j)
   lines[index]=f'IMPORTANT ARCHIVE ENTRY: label {key}, exact access code {value}. Preserve this code verbatim.\n';secrets[key]=value
 return ''.join(lines),secrets
PREFIX='Leia o arquivo de registros abaixo como dados. Localize as entradas rotuladas. Não invente códigos. Responda somente com o código solicitado, sem explicação.\n<arquivo>\n'
def prompt(doc,key):return PREFIX+doc+'\n</arquivo>\nQual é o código exato da entrada '+key+'?'

if os.environ.get('CONTEXT_MODELS'):
 MODELS=[m for m in MODELS if m[0] in os.environ['CONTEXT_MODELS'].split(',')]
if not MODELS:parser.error('No matching study model tags selected')
if req('/api/ps').get('models'):parser.error('Unload existing models before running the benchmark.')
for model,maximum in MODELS:
 meta=req('/api/show',{'model':model});thinking='thinking' in meta.get('capabilities',[])
 emit('MODEL '+model)
 levels=[x for x in [16384,32768,65536,131072,163840,262144] if x<=maximum and (x!=163840 or maximum==163840)]
 if os.environ.get('CONTEXT_LEVELS'):levels=[int(x) for x in os.environ['CONTEXT_LEVELS'].split(',') if int(x)<=maximum]
 if not levels or any(x<=0 for x in levels):parser.error('Select positive context sizes within the model cap')
 for ctx in levels:
  record={'model':model,'requested_context':ctx,'memory_before':memory(),'tests':[]};RESULTS.append(record);save()
  emit('CONTEXT '+model+' '+str(ctx))
  try:
   tiny,_=document(40)
   record['calibration']=call(model,ctx,prompt(tiny,'BEGIN1'),thinking,24)
   ps=req('/api/ps');record['loaded_models']=ps
   loaded=ps.get('models',[])
   if len(loaded)!=1:raise RuntimeError('Expected exactly one loaded model')
   actual=loaded[0].get('context_length');record['actual_context']=actual
   if actual is not None and actual<ctx:raise RuntimeError('Allocated context is smaller than requested')
   current=memory();record['memory_after_load']=current;save()
   if current['pressure']>=4 or current['swap_used_mb']-record['memory_before']['swap_used_mb']>2048:raise RuntimeError('Memory limit exceeded after loading')
   per_line=max(1,(record['calibration']['prompt_tokens']-70)/40)
   n=max(50,int(ctx*.82/per_line));doc,secrets=document(n)
   record['document']={'records':n,'sha256':hashlib.sha256(doc.encode()).hexdigest(),'expected':secrets,'target_fraction':.82}
   save()
   # Initial long-document processing is excluded from the six measured queries.
   record['prefill']=call(model,ctx,prompt(doc,'BEGIN1'),thinking,32);save()
   actual_tokens=record['prefill']['prompt_tokens'];record['occupancy']=round(actual_tokens/ctx,4)
   if actual_tokens>ctx-96:raise RuntimeError('Possible prompt truncation; do not certify this level')
   for key,value in secrets.items():
    row=call(model,ctx,prompt(doc,key),thinking,48)
    row['key']=key;row['expected']=value;row['passed']=value in row['response']['message']['content'];record['tests'].append(row);save()
    emit({'model':model,'context':ctx,'key':key,'passed':row['passed'],'tokens_s':row['tokens_per_second'],'seconds':row['seconds'],'prompt_tokens':row['prompt_tokens']})
   record['memory_after_tests']=memory()
   record['status']='ok' if all(x['passed'] for x in record['tests']) else 'retrieval_failed'
   record['prefill_passed']=secrets['BEGIN1'] in record['prefill']['response']['message']['content']
   emit({'model':model,'context':ctx,'status':record['status'],'occupancy':record['occupancy'],'memory':record['memory_after_tests']})
  except Exception as e:
   record['status']='error';record['error']=str(e);emit({'model':model,'context':ctx,'error':str(e)})
  save()
  try:
   req('/api/generate',{'model':model,'keep_alive':0},timeout=90)
   ps=req('/api/ps',timeout=30);record['after_unload']=ps;save()
   if ps.get('models'):raise RuntimeError('Model remains loaded')
  except Exception as e:emit('UNLOAD FAILED: '+str(e));raise
  if record['status']!='ok':break
 emit('MODEL FINISHED '+model)
emit('FINISHED')
