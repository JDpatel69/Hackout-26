import { ProgressRing } from '../shared';
export function RiskGauge({score}:{score:number}) { return <ProgressRing value={Math.max(0,Math.min(100,score))} label="confidence"/>; }
export default RiskGauge;
