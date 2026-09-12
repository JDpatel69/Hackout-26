import type { AppNotification } from '../types/models';
export const notifications: AppNotification[] = [
  { id:'not-1', userId:'op-ava', type:'credits', title:'Credits issued', message:'Green Valley Rice Farm has 126.4 tCO₂e ready to list.', isRead:false, createdAt:'2026-09-12T08:15:00', linkTo:'/farm-operator/credits' },
  { id:'not-2', userId:'op-ava', type:'verification', title:'Correction requested', message:'Terra Verde Coffee Estate needs one additional soil test.', isRead:false, createdAt:'2026-09-11T10:00:00', linkTo:'/farm-operator/verification' },
  { id:'not-3', userId:'ver-lina', type:'verification', title:'New evidence ready', message:'Blue River Vegetable Co-op submitted 5 evidence files.', isRead:false, createdAt:'2026-09-12T07:22:00', linkTo:'/verifier/requests' },
  { id:'not-4', userId:'res-sam', type:'system', title:'Dataset refresh complete', message:'Mekong vegetation time series is ready for analysis.', isRead:true, createdAt:'2026-09-10T15:10:00', linkTo:'/researcher/datasets' },
  { id:'not-5', userId:'inv-noah', type:'investment', title:'Portfolio updated', message:'Green Valley Rice Renewal has distributed a performance payout.', isRead:false, createdAt:'2026-09-11T13:35:00', linkTo:'/investor/portfolio' },
  { id:'not-6', userId:'inv-noah', type:'system', title:'Marketplace watchlist', message:'Three verified projects now match your medium-risk allocation.', isRead:true, createdAt:'2026-09-09T11:20:00', linkTo:'/investor/marketplace' }
];
