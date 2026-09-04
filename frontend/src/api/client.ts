const API=import.meta.env.VITE_API_URL||'/api';
let accessToken:string|null=null;
export const setAccessToken=(token:string|null)=>{accessToken=token};
async function request<T>(path:string,options:RequestInit={},retry=true):Promise<T>{
  const headers=new Headers(options.headers); if(accessToken)headers.set('Authorization',`Bearer ${accessToken}`); if(options.body)headers.set('Content-Type','application/json');
  const response=await fetch(`${API}${path}`,{...options,headers,credentials:'include',signal:options.signal});
  if(response.status===401&&retry&&!path.startsWith('/auth/')){const refreshed=await fetch(`${API}/auth/refresh`,{method:'POST',credentials:'include'});if(refreshed.ok){const body=await refreshed.json();setAccessToken(body.access);return request(path,options,false)}}
  if(!response.ok){const body=await response.json().catch(()=>null);throw new Error(body?.error?.message||body?.error?.details?.detail||`درخواست ناموفق بود (کد ${response.status})`)}
  return response.status===204?undefined as T:response.json();
}
export const api={get:<T>(path:string,signal?:AbortSignal)=>request<T>(path,{signal}),post:<T>(path:string,data?:unknown)=>request<T>(path,{method:'POST',body:data?JSON.stringify(data):undefined})};
