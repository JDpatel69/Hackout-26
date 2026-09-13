export const currency=(value:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
export const tonnes=(value:number)=>`${new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(value)} tCO₂e`;
export const shortDate=(value:string)=>new Intl.DateTimeFormat('en-US',{day:'numeric',month:'short',year:'numeric'}).format(new Date(value));
export const initials=(value:string)=>value.split(' ').map((part)=>part[0]).slice(0,2).join('').toUpperCase();
