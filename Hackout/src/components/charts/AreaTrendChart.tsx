import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
export function AreaTrendChart({data}:{data:{date:string;value:number}[]}) { return <div className="chart"><ResponsiveContainer><AreaChart data={data}><XAxis dataKey="date"/><YAxis/><Tooltip/><Area dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={.25}/></AreaChart></ResponsiveContainer></div>; }
export default AreaTrendChart;
