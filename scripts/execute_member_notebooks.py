"""Execute TV2/TV3 notebooks with one explicit environment and retain outputs."""
from datetime import datetime,timezone
import argparse
import json
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
kernel='aapl-coursework-tv2-tv3'
kernel_root=ROOT/'.venv/jupyter'
spec=kernel_root/'kernels'/kernel
spec.mkdir(parents=True,exist_ok=True)
(spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'AAPL Coursework TV2-TV3','language':'python'}),encoding='utf-8')
os.environ['JUPYTER_PATH']=str(kernel_root)
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.venv/jupyter_runtime')
os.environ.pop('PYTHONPATH',None)
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
os.environ['MPLBACKEND']='module://matplotlib_inline.backend_inline'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--member',choices=['2','3','all'],default='all')
    args=parser.parse_args()
    folder=ROOT/'logs/audit'/('member_notebooks_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    summary={'passed':False,'executable':sys.executable,'notebooks':[]}
    try:
        for name in ['02_TV2_Preprocessing_and_Audit.ipynb','03_TV3_LSTM_Development_and_Tests.ipynb']:
            if args.member != 'all' and not name.startswith('0'+args.member+'_'): continue
            path=ROOT/'notebooks'/name
            nb=nbformat.read(path,as_version=4)
            try:
                NotebookClient(nb,timeout=600,kernel_name=kernel,resources={'metadata':{'path':str(ROOT)}}).execute()
            finally:
                nbformat.write(nb,path)
            code_cells=[c for c in nb.cells if c.cell_type=='code']
            if any(c.execution_count is None for c in code_cells) or any(o.output_type=='error' for c in code_cells for o in c.outputs):
                raise RuntimeError(f'Notebook incomplete: {name}')
            summary['notebooks'].append({'name':name,'cells':len(nb.cells),'executed_code_cells':len(code_cells),'passed':True})
        summary['passed']=True
    finally:
        (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({**summary,'evidence':str(folder/'summary.json')},indent=2))


if __name__=='__main__': main()
