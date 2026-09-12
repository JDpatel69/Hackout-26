import { useEffect, useState } from 'react';
export const useMediaQuery=(query:string)=>{const [matches,setMatches]=useState(()=>matchMedia(query).matches);useEffect(()=>{const media=matchMedia(query);const listener=()=>setMatches(media.matches);listener();media.addEventListener('change',listener);return()=>media.removeEventListener('change',listener);},[query]);return matches;};
