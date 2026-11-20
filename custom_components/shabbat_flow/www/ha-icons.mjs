// Presentation only. HA owns icon rendering; no icon URLs or remote font requests.
import {request} from './transport.mjs';
const icons=new Map();
export const validIcon=value=>typeof value==='string'&&/^[a-z][a-z0-9_-]*:[a-z0-9_-]+$/.test(value)?value:null;
// Render in HA's document: adopting ha-icon into an iframe leaves its nested
// custom elements unregistered there. Cache the rendered SVG, never the live node.
const renderedIcons=new Map();
function nativeSvg(name){
 if(renderedIcons.has(name))return renderedIcons.get(name);
 const promise=new Promise(resolve=>{
  let host;
  try{
   const parent=window.parent;
   if(parent===window||!parent.customElements.get('ha-icon'))return resolve(null);
   host=parent.document.createElement('ha-icon');host.icon=name;
   host.style.cssText='position:fixed;inset:0;visibility:hidden;pointer-events:none;width:24px;height:24px';
   host.setAttribute('aria-hidden','true');parent.document.body.append(host);
  }catch{return resolve(null);}
  let attempts=0;
  const findSvg=root=>{for(const element of root.querySelectorAll('*')){if(element.localName==='svg'&&element.querySelector('path'))return element;if(element.shadowRoot){const found=findSvg(element.shadowRoot);if(found)return found;}}return null;};
  const poll=()=>{const svg=host.shadowRoot&&findSvg(host.shadowRoot);if(svg||++attempts>=40){host.remove();resolve(svg?.cloneNode(true)??null);}else setTimeout(poll,50);};poll();
 });
 renderedIcons.set(name,promise);return promise;
}
export function haIcon(value,fallback='mdi:home-outline'){
 const span=document.createElement('span');span.className='ha-assigned-icon';span.setAttribute('aria-hidden','true');
 span.textContent=fallback.includes('light')?'◉':fallback.includes('therm')?'♨':'◇';
 nativeSvg(validIcon(value)??fallback).then(svg=>{if(svg)span.replaceChildren(document.importNode(svg,true));});
 return span;
}
export function itemIcon(id,fallback){return haIcon(icons.get(id),fallback);}
export async function loadIcons(){
 try{
  const response=await request('/api/v2/household');if(!response.ok)return;
  const {inventory}=await response.json();
  for(const [items,prefix] of [[inventory.areas,'room_'],[inventory.entities,'load_']])for(const item of items){
   const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(item.id));
   const key=prefix+Array.from(new Uint8Array(bytes),n=>n.toString(16).padStart(2,'0')).join('').slice(0,20);
   icons.set(key,item.icon);icons.set(item.entity_id??item.id,item.icon);
  }
 }catch{/* Missing icons must not block planning or observation. */}
}
