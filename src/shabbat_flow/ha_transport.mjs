// The iframe receives a private MessagePort, not HA tokens or the hass object.
let port,sequence=0;
const pending=new Map();
const ready=new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(new Error('network')),15000);
  function connect(event){
    if(event.source!==window.parent||event.origin!==location.origin||event.data?.type!=='shabbat-flow-connect'||!event.ports[0])return;
    window.removeEventListener('message',connect);clearTimeout(timer);port=event.ports[0];
    port.onmessage=event=>{const message=event.data,job=pending.get(message?.id);if(!job)return;pending.delete(message.id);clearTimeout(job.timer);job.resolve({ok:message.status>=200&&message.status<300,status:message.status,json:async()=>message.body});};
    port.start();resolve();
  }
  window.addEventListener('message',connect);
  window.parent.postMessage({type:'shabbat-flow-ready'},location.origin);
});
export async function request(path,options={}){
  await ready;
  return new Promise((resolve,reject)=>{
    const id=++sequence,timer=setTimeout(()=>{pending.delete(id);reject(new Error('network'));},20000);
    pending.set(id,{resolve,timer});port.postMessage({id,path,method:options.method??'GET',body:options.body});
  });
}
