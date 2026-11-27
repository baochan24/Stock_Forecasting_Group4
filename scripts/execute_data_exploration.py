"""Execute notebooks/01_AAPL_Data_Exploration.ipynb and save its outputs."""
from pathlib import Path
import os
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
eda_python = Path(os.environ.get('TV1_NOTEBOOK_PYTHON', ROOT / '.venv/eda/Scripts/python.exe')).resolve()
if not eda_python.is_file():
    raise RuntimeError('Create .venv/eda and install notebooks/requirements-eda.txt first.')
if Path(sys.executable).resolve() != eda_python.resolve():
    import subprocess
    raise SystemExit(subprocess.call([str(eda_python), str(Path(__file__).resolve())]))
os.environ.pop('PYTHONPATH', None)
os.environ['MPLBACKEND'] = 'module://matplotlib_inline.backend_inline'
os.environ['YF_CACHE_DIR'] = str(ROOT / '.venv/yf_cache')
kernel_root = ROOT / '.venv/jupyter'
spec_dir = kernel_root / 'kernels/aapl-eda-project'
spec_dir.mkdir(parents=True, exist_ok=True)
(spec_dir/'kernel.json').write_text(json.dumps({'argv':[str(eda_python),'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'AAPL EDA (Python 3.13)','language':'python'}),encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(kernel_root)
os.environ['JUPYTER_RUNTIME_DIR'] = str(ROOT / '.venv/jupyter_runtime')
import nbformat
from nbclient import NotebookClient
path = ROOT / 'notebooks/01_AAPL_Data_Exploration.ipynb'
nb = nbformat.read(path,as_version=4)
nb.metadata['kernelspec'] = {'display_name':'AAPL EDA (Python 3.13)', 'language':'python', 'name':'aapl-eda-project'}
client = NotebookClient(nb,timeout=240,kernel_name='aapl-eda-project',resources={'metadata':{'path':str(ROOT)}})
try:
    client.execute()
finally:
    nbformat.write(nb,path)
print('Executed:', path)
