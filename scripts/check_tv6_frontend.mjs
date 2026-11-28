// Real Chrome + real API, using built-in Node CDP/WebSocket; no browser packages.
import {spawn,execFileSync} from 'node:child_process';
import {createServer} from 'node:net';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2);
if(args.length%2||args.some((a,i)=>i%2===0&&!['--python','--browser'].includes(a)))throw new Error('Usage: node scripts/check_tv6_frontend.mjs [--python interpreter] [--browser executable]');
const option=name=>{const i=args.indexOf(name);return i<0?null:args[i+1];};
const python=option('--python')||process.env.TV6_PYTHON||['.venv/tv6_demo/Scripts/python.exe','.venv/tv4_clean/Scripts/python.exe','.venv/bin/python'].map(p=>path.join(root,p)).find(existsSync);
const browser=option('--browser')||process.env.TV6_BROWSER||[
  path.join(process.env.PROGRAMFILES||'C:/Program Files','Google/Chrome/Application/chrome.exe'),
  path.join(process.env['PROGRAMFILES(X86)']||'C:/Program Files (x86)','Microsoft/Edge/Application/msedge.exe'),
  path.join(process.env.LOCALAPPDATA||'','Google/Chrome/Application/chrome.exe')].find(existsSync);
if(!python||!existsSync(python))throw new Error('Python not found; supply --python with an existing environment interpreter.');
if(!browser||!existsSync(browser))throw new Error('Browser not found; supply --browser with Chrome or Edge executable.');
const stamp=new Date().toISOString().replace(/[-:.]/g,'');
const folder=path.join(root,'logs/audit','tv6_item9_'+stamp);
await mkdir(folder,{recursive:true});
const port=()=>new Promise(resolve=>{const server=createServer();server.listen(0,'127.0.0.1',()=>{const p=server.address().port;server.close(()=>resolve(p));});});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const processes=[],logs=[],checks=[],consoleErrors=[],requests=[];
function launch(command,args){const child=spawn(command,args,{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});child.stdout.on('data',d=>logs.push(d.toString()));child.stderr.on('data',d=>logs.push(d.toString()));processes.push(child);return child;}
async function waitFor(fn,label,timeout=90000){const end=Date.now()+timeout;let error;while(Date.now()<end){try{if(await fn())return;}catch(e){error=e;}await sleep(200);}throw new Error('Timeout: '+label+' '+(error?.message||''));}
let ws;let api;
try{
  const apiPort=await port(),uiPort=await port(),debugPort=await port();
  api=launch(python,['scripts/run_tv6_api.py','--port',String(apiPort)]);
  launch(python,['scripts/run_tv6_frontend.py','--port',String(uiPort),'--api-port',String(apiPort)]);
  await waitFor(async()=> (await fetch(`http://127.0.0.1:${uiPort}/`)).ok,'UI server');
  await waitFor(async()=> (await fetch(`http://127.0.0.1:${apiPort}/api/v1/health`)).ok,'API startup');
  launch(browser,['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port='+debugPort,'--user-data-dir='+path.join(root,'.venv','tv6_browser_'+stamp),'about:blank']);
  let targets;await waitFor(async()=>{targets=await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json();return targets.some(t=>t.type==='page');},'Chrome');
  ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let id=0;const pending=new Map();
  const send=(method,params={})=>new Promise((resolve,reject)=>{const key=++id;const timer=setTimeout(()=>{pending.delete(key);reject(new Error('CDP timeout '+method));},120000);pending.set(key,{resolve,reject,timer});ws.send(JSON.stringify({id:key,method,params}));});
  ws.onmessage=event=>{const data=JSON.parse(event.data);if(data.id){const p=pending.get(data.id);if(p){clearTimeout(p.timer);pending.delete(data.id);data.error?p.reject(new Error(JSON.stringify(data.error))):p.resolve(data.result);}}else if(data.method==='Runtime.exceptionThrown')consoleErrors.push(data.params.exceptionDetails);else if(data.method==='Network.requestWillBeSent'&&data.params.request.url.includes('/api/v1/'))requests.push(data.params.request);};
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  const ready=(expression,label)=>waitFor(()=>evaluate(expression),label);
  const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const check=async(name,expression)=>{assert.equal(await evaluate(expression),true,name);checks.push({name,passed:true});};
  const shot=async(name)=>{const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(folder,name),Buffer.from(r.data,'base64'));};
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1600,height:1100,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:`http://127.0.0.1:${uiPort}/`});
  await ready("document.querySelector('#connection')?.textContent==='API sẵn sàng'&&!document.querySelector('#run').disabled",'API readiness + UI');
  await click('#run');await ready("document.querySelectorAll('#prediction-table tbody tr').length===3",'h1 prediction');
  await check('one step, three methods, actual comparison',"document.querySelectorAll('#prediction-cards .prediction-row').length===3&&document.querySelector('#prediction-table').textContent.includes('Đã đối chiếu')");
  await shot('forecast_h1_desktop.png');
  await click('[name=horizon][value="5"]');
  await ready("!document.querySelector('#run').disabled",'h5 origins');
  await check('h5 disables and unchecks CNN, clears old result',"document.querySelector('[name=method][value=cnn]').disabled&&!document.querySelector('[name=method][value=cnn]').checked&&document.querySelector('#export').disabled&&document.querySelectorAll('#prediction-table tbody tr').length===0");
  await click('#run');await ready("document.querySelectorAll('#prediction-table tbody tr').length===10",'h5 prediction');
  await check('five steps, no CNN, actual API target dates',"!document.querySelector('#prediction-table').textContent.includes('CNN')&&document.querySelector('#prediction-table').textContent.includes('T+5')");
  await shot('forecast_h5_desktop.png');
  await click('[href="#compare"]');await click('#metric-form button[type=submit]');
  await ready("document.querySelectorAll('#metric-table tbody tr').length===12",'h5 metrics');
  await check('full metrics display counts, scope and evaluation phase',"document.querySelector('#metric-table').textContent.includes('498')&&document.querySelector('#metric-table').textContent.includes('2490')&&document.querySelector('#metric-context').textContent.includes('TOÀN TẬP RELEASE')&&document.querySelector('#metric-table').textContent.includes('không độc lập')");
  await evaluate("document.querySelector('#metric-scope').value='range';document.querySelector('#metric-scope').dispatchEvent(new Event('change'))");
  await click('#metric-form button[type=submit]');await ready("document.querySelectorAll('#metric-table tbody tr').length===12",'selected metrics');
  await check('selected range is distinguished',"document.querySelector('#metric-context').textContent.includes('2025-06-01 — 2025-06-16')&&!document.querySelector('#metric-context').textContent.includes('TOÀN TẬP RELEASE')");
  await click('#load-experiment');await ready("document.querySelector('#experiment-content svg')!==null",'experiment history');
  await shot('comparison_desktop.png');
  await click('[href="#errors"]');await click('#load-errors');await ready("document.querySelectorAll('#error-table tbody tr').length>0",'stored errors');
  await check('error pagination scope and matched rows',"document.querySelector('#error-context').textContent.includes('trong trang này')&&document.querySelector('#errors-prev').disabled");
  await click('[href="#data"]');await check('data explorer shows real snapshot',"document.querySelector('#dataset-info').textContent.includes('2766')&&document.querySelectorAll('#data-table tbody tr').length===100");await click('#data-next');await check('data pagination works',"document.querySelector('#data-page-info').textContent.startsWith('101')");
  await click('[href="#journal"]');await check('journal retains actual completed requests',"document.querySelectorAll('#journal-table tbody tr').length===13");
  await click('[href="#model"]');await click('#load-trace');await ready("document.querySelectorAll('#trace-table tbody tr').length===30",'LSTM trace');
  await check('trace verified',"document.querySelector('#trace-context').textContent.includes('verified: true')");await shot('lstm_trace_desktop.png');
  await click('[href="#forecast"]');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(300);
  await check('mobile no page horizontal overflow',"document.documentElement.scrollWidth<=window.innerWidth");await shot('forecast_mobile.png');
  const predictionRequests=requests.filter(r=>r.url.endsWith('/predictions')).map(r=>JSON.parse(r.postData));
  assert.equal(predictionRequests.length,2);assert.deepEqual(predictionRequests.map(r=>r.forecast_length),[1,5]);
  assert.ok(predictionRequests.every(r=>!('target_values' in r)&&!('checkpoint' in r)&&!('input_values' in r)));
  checks.push({name:'browser sends input-only prediction contract',passed:true});
  // Fail the proxy by stopping only the API process started by this test.
  api.kill();await new Promise(resolve=>api.once('exit',resolve));
  await click('#run');await ready("!document.querySelector('#notice').hidden",'API outage visible');
  await ready("!document.querySelector('#run').disabled",'failed prediction settled');
  await check('outage shown, no stale prediction/export',"document.querySelector('#notice').textContent.includes('Backend API')&&document.querySelector('#export').disabled&&document.querySelectorAll('#prediction-table tbody tr').length===0");
  await shot('api_unavailable.png');
  assert.equal(consoleErrors.length,0,JSON.stringify(consoleErrors));checks.push({name:'no uncaught browser exceptions',passed:true});
  const sourcePaths=['frontend/index.html','frontend/styles.css','frontend/app.js','frontend/api_client/client.js','frontend/prediction_results/charts.js','frontend/forecast_selection/state.js','scripts/run_tv6_frontend.py','scripts/check_tv6_frontend.mjs','tests/frontend/test_ui_contract.mjs'];
  const source_hashes=Object.fromEntries(await Promise.all(sourcePaths.map(async p=>[p,createHash('sha256').update(await readFile(path.join(root,p))).digest('hex')])));
  const tests=execFileSync(process.execPath,['--test','tests/frontend/test_ui_contract.mjs'],{cwd:root,windowsHide:true,encoding:'utf8'});await writeFile(path.join(folder,'javascript_tests.tap'),tests);
  const integrity=execFileSync(python,['-c',"from backend.artifacts.research_release import validate_release;from backend.services.results.release_results import ReleaseResults;from pathlib import Path;r=validate_release(Path.cwd());ReleaseResults(Path.cwd()).validate(r);print(r['semantic_sha256'])"],{cwd:root,windowsHide:true,encoding:'utf8'}).trim();
  const summary={passed:true,browser:'Chromium headless via CDP',browser_executable:browser,python_executable:python,real_api:true,checks:checks.length,unit_tests:5,release_sha256:integrity,training:false,independent_holdout:false,source_hashes,evidence:path.relative(root,folder).replaceAll('\\','/')};
  await writeFile(path.join(folder,'checks.json'),JSON.stringify(checks,null,2));await writeFile(path.join(folder,'prediction_requests.json'),JSON.stringify(predictionRequests,null,2));await writeFile(path.join(folder,'summary.json'),JSON.stringify(summary,null,2));await writeFile(path.join(root,'logs/audit/tv6_item9_latest.json'),JSON.stringify({evidence:summary.evidence+'/summary.json'},null,2));console.log(JSON.stringify(summary));
}catch(error){await writeFile(path.join(folder,'failure.json'),JSON.stringify({error:error.stack,checks,consoleErrors},null,2));throw error;}
finally{ws?.close();for(const child of processes)if(child.exitCode===null)child.kill();await writeFile(path.join(folder,'server_browser.log'),logs.join(''));}
