const routes=new Map([
  ['GET /api/v2/execution','shabbat_flow/execution'],
  ['POST /api/v2/execution','shabbat_flow/execution'],
  ['POST /api/v2/pdf','shabbat_flow/pdf'],
  ['GET /api/v2/observe','shabbat_flow/observe'],
  ['POST /api/v2/observe','shabbat_flow/observe'],
  ['GET /api/v2/upcoming','shabbat_flow/upcoming'],
  ['GET /api/v2/household','shabbat_flow/household'],
  ['POST /api/v2/household','shabbat_flow/household'],
  ['POST /api/v2/household_plan','shabbat_flow/household_plan'],
  ['GET /api/v2/example','shabbat_flow/sample'],
  ['GET /api/v2/i18n','shabbat_flow/catalog'],
  ['GET /api/v2/calendar','shabbat_flow/calendar'],
  ['POST /api/v2/preview','shabbat_flow/preview'],
]);
class ShabbatFlowPanel extends HTMLElement{
  constructor(){super();this.attachShadow({mode:'open'});this._connect=this._connect.bind(this);}
  set hass(value){this._hass=value;this._render();}
  connectedCallback(){window.addEventListener('message',this._connect);this._render();}
  disconnectedCallback(){window.removeEventListener('message',this._connect);this._port?.close();this._port=null;this._frame=null;this.shadowRoot.replaceChildren();}
  _render(){
    if(!this.isConnected||!this._hass)return;
    const report=new URLSearchParams(location.search).get('report');
    const reportId=report&&/^[a-f0-9]{32}$/.test(report)?report:null;
    if(this._frame){if(this._report!==reportId){this._report=reportId;this._frame.src=new URL(reportId?'./observation.html?run='+reportId:'./household.html',import.meta.url).href;}return;}
    const style=document.createElement('style');style.textContent=':host{display:flex;flex-direction:column;height:100vh;height:100dvh;min-height:0}header{display:flex;align-items:center;padding:8px 12px;gap:12px;background:var(--primary-background-color);color:var(--primary-text-color)}button{font:inherit;padding:8px 12px;border:0;border-radius:8px;cursor:pointer}iframe{flex:1;width:100%;min-height:0;border:0;background:white}';
    const header=document.createElement('header'),button=document.createElement('button');button.textContent='☰';button.setAttribute('aria-label',this._hass.language==='he'?'פתיחת תפריט':'Open sidebar');
    button.onclick=()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    const title=document.createElement('span');title.textContent='Shabbat Flow';header.append(button,title);
    this._frame=document.createElement('iframe');this._frame.title='ShabbatFlow';this._report=reportId;this._frame.src=new URL('./household.html',import.meta.url).href;if(reportId)this._frame.src=new URL('./observation.html?run='+reportId,import.meta.url).href;
    this.shadowRoot.append(style,header,this._frame);
  }
  _connect(event){
    if(event.origin!==location.origin||event.source!==this._frame?.contentWindow||event.data?.type!=='shabbat-flow-ready')return;
    this._port?.close();const channel=new MessageChannel();this._port=channel.port1;
    channel.port1.onmessage=async event=>{
      const message=event.data;
      if(!message||!Number.isSafeInteger(message.id))return;
      const route=routes.get(`${message.method} ${message.path}`);
      let status=200,body;
      try{
        if(!route||!this._hass.user?.is_admin){status=403;body={error:'forbidden'};}
        else if(message.body!==undefined&&(typeof message.body!=='string'||new TextEncoder().encode(message.body).length>131072)){status=413;body={error:'too_large'};}
        else body=await this._hass.callApi(message.method,route,message.body===undefined?undefined:JSON.parse(message.body));
      }catch(error){status=Number(error.status_code)||400;body={error:typeof error.body?.error==='string'?error.body.error:'invalid_request'};}
      channel.port1.postMessage({id:message.id,status,body});
    };
    channel.port1.start();event.source.postMessage({type:'shabbat-flow-connect'},location.origin,[channel.port2]);
  }
}
if(!customElements.get('shabbat-flow-panel'))customElements.define('shabbat-flow-panel',ShabbatFlowPanel);
