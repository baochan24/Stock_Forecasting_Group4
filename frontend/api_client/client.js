// Same-origin local proxy. No model, target construction or metric calculation here.
export class ApiError extends Error {
  constructor(message,status,requestId){super(message);this.status=status;this.requestId=requestId;}
}
export async function request(path,{body,signal}={}){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),90000);
  const abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});
  try {
    const response=await fetch('/api/v1'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,signal:controller.signal});
    const data=await response.json();
    if(!response.ok)throw new ApiError(data.error?.message||'API không thể xử lý yêu cầu.',response.status,data.request_id);
    return data;
  } catch(error){
    if(error instanceof ApiError)throw error;
    throw new ApiError(error.name==='AbortError'?'Yêu cầu đã hủy hoặc quá thời gian.':'Không kết nối được API. Kiểm tra backend đang chạy.',0,null);
  } finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
}
export function query(values){const params=new URLSearchParams();for(const [key,value] of Object.entries(values)){if(value===undefined||value===null||value==='')continue;for(const item of Array.isArray(value)?value:[value])params.append(key,item);}return '?'+params;}
