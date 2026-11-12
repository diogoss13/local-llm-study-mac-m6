#!/usr/bin/env python3
"""Adapted reproduction runner; historical prompts and task IDs are unchanged."""
import argparse,json,time,urllib.request,pathlib
parser=argparse.ArgumentParser(description="Repeat the six-task benchmark; original Portuguese prompts are preserved.")
parser.add_argument('--base-url',default='http://127.0.0.1:11434')
parser.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path('outputs/short'))
parser.add_argument('--models',help='Comma-separated installed study model tags')
ARGS=parser.parse_args()
out=ARGS.output_dir;out.mkdir(parents=True,exist_ok=True)
base=ARGS.base_url.rstrip('/')
def req(path,data=None,timeout=480):
 r=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(r,timeout=timeout) as f:return json.load(f)
models=['qwen2.5-coder:14b','gemma4:12b','qwen3.5:9b-q4_K_M','deepseek-coder-v2:16b']
prompts=[('raciocinio','Responda em português em uma frase: 3 caixas com 7 peças cada, retirando 4 peças do total, quantas restam?'),('codigo','Escreva uma função Python chamada unicos que recebe uma lista de inteiros e remove duplicatas preservando a ordem. Sem bibliotecas.'),('portugues','Explique em português, em cerca de 100 palavras, a diferença entre memória RAM e armazenamento SSD.'),('json','Retorne apenas JSON válido com o formato {"total":numero,"aprovados":[nomes]}. Dados: Ana nota 8, Beto nota 4, Carla nota 9. Aprovados têm nota maior ou igual a 7. Total é a quantidade de alunos.'),('resumo','Resuma em português em três itens: o projeto usa modelos locais no SSD; apenas um modelo deve ficar na memória; a primeira resposta carrega os pesos; as respostas seguintes permitem medir a geração.'),('planejamento','Em português, descreva cinco passos para organizar cópias de segurança dos documentos pessoais. Use cerca de 100 palavras.')]
if ARGS.models:
 requested=ARGS.models.split(',')
 unknown=set(requested)-set(models)
 if unknown:parser.error('Unknown study model tags: '+', '.join(sorted(unknown)))
 models=[m for m in models if m in requested]
if req('/api/ps').get('models'):parser.error('Unload existing models before running the benchmark.')
results=[]
for model in models:
 print('LOADING '+model,flush=True)
 meta=req('/api/show',{'model':model})
 for i,(kind,prompt) in enumerate([('aquecimento','Responda apenas: pronto.')]+prompts):
  data={'model':model,'messages':[{'role':'user','content':prompt}],'stream':False,'keep_alive':'15m','options':{'num_ctx':4096,'num_predict':256,'temperature':0}}
  if 'thinking' in meta.get('capabilities',[]):data['think']=False
  start=time.monotonic()
  try:
   r=req('/api/chat',data)
   row={'model':model,'test':kind,'measured':i>0,'seconds':round(time.monotonic()-start,3),'tokens_per_second':round(r.get('eval_count',0)*1e9/r['eval_duration'],2) if r.get('eval_duration') else None,'response':r}
  except Exception as e:row={'model':model,'test':kind,'measured':i>0,'seconds':round(time.monotonic()-start,3),'error':str(e)}
  results.append(row)
  (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
  print(json.dumps({k:v for k,v in row.items() if k!='response'},ensure_ascii=False),flush=True)
  if 'error' in row:break
 if 'tools' in meta.get('capabilities',[]):
  data['messages']=[{'role':'user','content':'Consulte a temperatura em Curitiba usando a ferramenta fornecida.'}]
  data['tools']=[{'type':'function','function':{'name':'consultar_temperatura','description':'Consulta temperatura por cidade','parameters':{'type':'object','properties':{'cidade':{'type':'string'}},'required':['cidade']}}}]
  try:
   r=req('/api/chat',data);results.append({'model':model,'test':'ferramenta','measured':False,'response':r})
   print('TOOL '+model+' '+json.dumps(r.get('message'),ensure_ascii=False),flush=True)
  except Exception as e:results.append({'model':model,'test':'ferramenta','measured':False,'error':str(e)})
  (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 try:
  req('/api/generate',{'model':model,'keep_alive':0},timeout=60)
  print('UNLOADED '+model+' '+json.dumps(req('/api/ps')),flush=True)
 except Exception as e:print('UNLOAD ERROR '+str(e),flush=True);break
print('FINISHED',flush=True)
