import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from 'recharts';
export function ComparisonRadar({data}:{data:{subject:string;value:number}[]}) { return <div className="chart"><ResponsiveContainer><RadarChart data={data}><PolarGrid/><PolarAngleAxis dataKey="subject"/><Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={.3}/></RadarChart></ResponsiveContainer></div>; }
export default ComparisonRadar;
