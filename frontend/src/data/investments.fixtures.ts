import type { Investment, Transaction } from '../types/models';
export const investments: Investment[] = [
  { id: 'inv-1', investorId: 'inv-noah', projectId: 'project-green-valley', amountInvested: 1800, creditsPurchased: 64.3, investedAt: '2026-02-14', status: 'active', currentValue: 1985, returnPercent: 10.3 },
  { id: 'inv-2', investorId: 'inv-noah', projectId: 'project-highland', amountInvested: 2400, creditsPurchased: 77.4, investedAt: '2026-04-07', status: 'active', currentValue: 2580, returnPercent: 7.5 },
  { id: 'inv-3', investorId: 'inv-noah', projectId: 'project-golden', amountInvested: 1200, creditsPurchased: 46.2, investedAt: '2026-06-18', status: 'active', currentValue: 1310, returnPercent: 9.2 }
];
export const transactions: Transaction[] = [
  { id: 'txn-1', investorId: 'inv-noah', type: 'investment', amount: 1800, relatedProjectId: 'project-green-valley', date: '2026-02-14', status: 'completed' },
  { id: 'txn-2', investorId: 'inv-noah', type: 'investment', amount: 2400, relatedProjectId: 'project-highland', date: '2026-04-07', status: 'completed' },
  { id: 'txn-3', investorId: 'inv-noah', type: 'payout', amount: 185, relatedProjectId: 'project-green-valley', date: '2026-07-01', status: 'completed' },
  { id: 'txn-4', investorId: 'inv-noah', type: 'investment', amount: 1200, relatedProjectId: 'project-golden', date: '2026-06-18', status: 'completed' },
  { id: 'txn-5', investorId: 'inv-noah', type: 'credit_retirement', amount: 68, relatedProjectId: 'project-highland', date: '2026-08-12', status: 'completed' },
  { id: 'txn-6', investorId: 'inv-noah', type: 'payout', amount: 116, relatedProjectId: 'project-golden', date: '2026-08-29', status: 'pending' },
  { id: 'txn-7', investorId: 'inv-noah', type: 'investment', amount: 850, relatedProjectId: 'project-redwood', date: '2026-09-02', status: 'completed' },
  { id: 'txn-8', investorId: 'inv-noah', type: 'withdrawal', amount: 500, date: '2026-09-05', status: 'completed' }
];
