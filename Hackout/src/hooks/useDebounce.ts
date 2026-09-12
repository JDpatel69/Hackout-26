import { useEffect, useState } from 'react';
export const useDebounce=<T,>(value:T,ms=250)=>{const [delayed,setDelayed]=useState(value);useEffect(()=>{const id=window.setTimeout(()=>setDelayed(value),ms);return()=>clearTimeout(id);},[value,ms]);return delayed;};
