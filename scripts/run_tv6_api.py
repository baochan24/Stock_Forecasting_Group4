"""Run the historical research API on localhost; never train models."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

if __name__=='__main__':
    import uvicorn
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    uvicorn.run('backend.api.app:app',host='127.0.0.1',port=args.port,workers=1,log_level='info')
