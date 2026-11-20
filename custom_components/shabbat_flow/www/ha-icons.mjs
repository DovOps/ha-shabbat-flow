// Presentation only. HA owns icon rendering; no icon URLs or remote font requests.
import {request} from './transport.mjs';
const icons=new Map();
export const validIcon=value=>typeof value==='string'&&/^[a-z][a-z0-9_-]*:[a-z0-9_-]+$/.test(value)?value:null;
export function haIcon(value,fallback='mdi:home-outline'){
 const span=document.createElement('span');span.className='ha-assigned-icon';span.setAttribute('aria-hidden','true');
 try{
  if(window.parent!==window&&window.parent.customElements.get('ha-icon')){
   const icon=window.parent.document.createElement('ha-icon');icon.icon=validIcon(value)??fallback;span.append(icon);return span;
  }
 }catch{/* Standalone or unavailable HA frontend: retain a decorative fallback. */}
 span.textContent=fallback.includes('light')?'◉':fallback.includes('therm')?'♨':'◇';return span;
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
