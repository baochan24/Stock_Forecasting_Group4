import test from 'node:test';
import assert from 'node:assert/strict';
import {predictionBody,methodsForHorizon,joinedRows,csv} from '../../frontend/forecast_selection/state.js';
import {escape,lineChart,table} from '../../frontend/prediction_results/charts.js';
import {request,ApiError,query} from '../../frontend/api_client/client.js';

test('five steps excludes CNN; request has input-only allowlisted fields',()=>{
  const body=predictionBody('release','2025-06-16',5,['lstm','cnn','persistence'],42);
  assert.deepEqual(body.methods,['lstm','persistence']);
  assert.deepEqual(Object.keys(body),['release_id','forecast_origin','forecast_length','methods','seed']);
  assert.deepEqual(methodsForHorizon(['cnn'],1),['cnn']);
  assert.throws(()=>predictionBody('release','',1,['lstm'],42));
  assert.throws(()=>predictionBody('release','2025-06-16',5,['cnn'],42));
});
test('comparison joins by method, target and horizon, not array position',()=>{
  const r={predictions:[{method:'lstm',target_date:'2025-06-17',horizon_step:1,predicted_price:10},{method:'persistence',target_date:'2025-06-17',horizon_step:1,predicted_price:12}],comparison:[{method:'persistence',target_date:'2025-06-17',horizon_step:1,actual_price:11,error_usd:1},{method:'lstm',target_date:'2025-06-17',horizon_step:1,actual_price:11,error_usd:-1}]};
  assert.equal(joinedRows(r)[0].error_usd,-1);assert.equal(joinedRows(r)[1].error_usd,1);
  assert.match(csv(joinedRows(r)),/actual_price,error_usd/);
});
test('untrusted metadata escaped in charts and tables',()=>{
  assert.equal(escape('<script>'), '&lt;script&gt;');
  assert.ok(!table(['x'],[['<img onerror=alert(1)>']]).includes('<img'));
  assert.ok(!lineChart([{name:'actual',values:[1,2]}],['<script>','b'],{title:'<script>'}).includes('<script>'));
});
test('query preserves repeated method params and canonical dates',()=>{
  const p=new URLSearchParams(query({methods:['lstm','persistence'],origin_from:'2025-06-01',empty:null}).slice(1));
  assert.deepEqual(p.getAll('methods'),['lstm','persistence']);assert.equal(p.get('origin_from'),'2025-06-01');assert.ok(!p.has('empty'));
});
test('API surfaces domain errors and sends no target',async()=>{
  const saved=globalThis.fetch;let sent;
  globalThis.fetch=async(url,options)=>{sent=JSON.parse(options.body);return {ok:false,status:422,json:async()=>({request_id:'abc',error:{message:'Invalid origin'}})};};
  try{await assert.rejects(request('/predictions',{body:predictionBody('r','2025-06-16',1,['lstm'],42)}),e=>e instanceof ApiError&&e.status===422&&e.requestId==='abc');assert.ok(!('target_values' in sent));}finally{globalThis.fetch=saved;}
});
