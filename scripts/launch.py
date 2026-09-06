import os,sys,pathlib,socket,threading,time,urllib.request,subprocess,json
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
import uvicorn
sock=socket.socket()
try:sock.bind(('127.0.0.1',8765))
except OSError:sock.bind(('127.0.0.1',0))
port=sock.getsockname()[1];url=f'http://127.0.0.1:{port}'
(ROOT/'backend/data/last_launch.json').write_text(json.dumps({'url':url,'pid':os.getpid()}))
def browser():
    for _ in range(100):
        try:
            with urllib.request.urlopen(url+'/api/health',timeout=1) as r:
                if json.load(r)['status']=='ok':
                    print(f'Battery MRI ready: {url}',flush=True)
                    if not os.environ.get('BATTERY_MRI_NO_BROWSER'):
                        opened=subprocess.run(['open',url],capture_output=True,text=True)
                        if opened.returncode:print(f'Browser could not open automatically in this session. Open this address in your browser: {url}',flush=True)
                    return
        except Exception:time.sleep(.2)
    print('Startup did not finish. See the error above.',flush=True)
threading.Thread(target=browser,daemon=True).start()
uvicorn.Server(uvicorn.Config('backend.main:app',log_level='warning')).run(sockets=[sock])
