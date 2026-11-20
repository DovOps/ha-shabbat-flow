export function formatOffset(value){const n=Math.abs(value);return `${value<0?'-':''}${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;}
export function parseOffset(value,min=-Infinity,max=Infinity){
 const m=/^(-?)(\d{2,3}):([0-5]\d)$/.exec(value);if(!m)return null;
 const n=(m[1]?-1:1)*(Number(m[2])*60+Number(m[3]));return n>=min&&n<=max?n:null;
}
export function offsetControl(input,value,min,max,onChange,error,onInvalid=()=>{}){
 const clean=input.cloneNode(false);input.replaceWith(clean);input=clean;
 input.type='text';input.value=formatOffset(value);input.placeholder='HH:MM';input.dir='ltr';
 input.oninput=()=>{const n=parseOffset(input.value,min,max);input.setCustomValidity(n===null?error:'');input.setAttribute('aria-invalid',String(n===null));if(n!==null)onChange(n);else onInvalid();};
}
