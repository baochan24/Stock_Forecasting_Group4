"""Serve the TV6 static UI and a fixed localhost API proxy; no dependencies."""
import argparse,json,urllib.request,urllib.error
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class FrontendHandler(SimpleHTTPRequestHandler):
    api_port=8000

    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        super().end_headers()

    def proxy(self):
        if not self.path.startswith('/api/v1/'):
            self.send_error(404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<0 or size>16384:self.send_error(413);return
            body=self.rfile.read(size) if self.command=='POST' else None
            req=urllib.request.Request(f'http://127.0.0.1:{self.api_port}'+self.path,data=body,method=self.command,headers={'Content-Type':'application/json'})
            try:response=urllib.request.urlopen(req,timeout=95)
            except urllib.error.HTTPError as error:response=error
            with response:
                data=response.read();self.send_response(response.status)
                self.send_header('Content-Type',response.headers.get('Content-Type','application/json'))
                self.send_header('Content-Length',str(len(data)))
                if response.headers.get('X-Request-ID'):self.send_header('X-Request-ID',response.headers['X-Request-ID'])
                self.end_headers();self.wfile.write(data)
        except (OSError,ValueError):
            data=json.dumps({'error':{'message':'Backend API chưa kết nối được. Chạy scripts/run_tv6_api.py rồi kết nối lại.'}}).encode()
            self.send_response(503);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith('/api/'):return self.proxy()
        return super().do_GET()

    def do_POST(self):return self.proxy()

    def list_directory(self,path):self.send_error(404);return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=5173);parser.add_argument('--api-port',type=int,default=8000)
    args=parser.parse_args();FrontendHandler.api_port=args.api_port
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(FrontendHandler,directory=str(ROOT/'frontend')))
    print(f'AAPL Forecast Lab: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
