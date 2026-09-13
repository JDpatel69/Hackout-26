import { ChevronRight } from 'lucide-react'; import { Link } from 'react-router-dom';
export function Breadcrumb({items}:{items:{label:string;to?:string}[]}) { return <nav aria-label="Breadcrumb" className="tiny muted" style={{display:'flex',gap:6,alignItems:'center'}}>{items.map((item,index)=><span key={`${item.label}-${index}`} style={{display:'flex',gap:6,alignItems:'center'}}>{item.to?<Link to={item.to}>{item.label}</Link>:<span>{item.label}</span>}{index<items.length-1&&<ChevronRight size={12}/>}</span>)}</nav>; }
export default Breadcrumb;
