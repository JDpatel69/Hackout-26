import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
export function AllocationDonut({data}:{data:{name:string;value:number}[]}) { return <div className="chart chart-short"><ResponsiveContainer><PieChart><Pie data={data} dataKey="value" innerRadius={48} outerRadius={76}>{data.map((entry,index)=><Cell key={entry.name} fill={['var(--accent)','var(--accent-2)','#60a5fa','#a78bfa'][index%4]}/>)}</Pie><Tooltip/></PieChart></ResponsiveContainer></div>; }
export default AllocationDonut;
