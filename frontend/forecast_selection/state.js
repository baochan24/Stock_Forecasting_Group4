export function methodsForHorizon(methods,horizon){return methods.filter(m=>horizon===1||m!=='cnn');}
export function predictionBody(releaseId,origin,horizon,methods,seed){
  const allowed=methodsForHorizon(methods,horizon);
  if(!origin)throw new Error('Chọn ngày gốc hợp lệ.');
  if(![1,5].includes(horizon)||![42,123,456].includes(seed)||!allowed.length)throw new Error('Chọn ít nhất một phương pháp và chế độ hợp lệ.');
  return {release_id:releaseId,forecast_origin:origin,forecast_length:horizon,methods:allowed,seed};
}
export function comparisonKey(row){return `${row.method}:${row.target_date}:${row.horizon_step}`;}
export function joinedRows(result){const actual=new Map(result.comparison.map(row=>[comparisonKey(row),row]));return result.predictions.map(row=>({...row,...actual.get(comparisonKey(row))}));}
export function csv(rows){const fields=['release_id','forecast_origin','target_date','method','horizon_step','predicted_price','actual_price','error_usd','run_id'];const cell=v=>'"'+String(v??'').replaceAll('"','""')+'"';return '\ufeff'+[fields.join(','),...rows.map(row=>fields.map(key=>cell(row[key])).join(','))].join('\r\n');}
