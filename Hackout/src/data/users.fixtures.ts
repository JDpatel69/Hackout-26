import type { User } from '../types/models';

export const users: User[] = [
  { id: 'op-ava', name: 'Ava Patel', email: 'ava@terraledger.demo', avatarUrl: '', role: 'farm_operator', organization: 'Green Valley Collective', createdAt: '2024-02-10', lastLoginAt: '2026-09-12' },
  { id: 'ver-lina', name: 'Lina Okafor', email: 'lina@terraledger.demo', avatarUrl: '', role: 'verifier', organization: 'EcoAudit Partners', createdAt: '2023-05-18', lastLoginAt: '2026-09-12' },
  { id: 'res-sam', name: 'Dr. Sam Lee', email: 'sam@terraledger.demo', avatarUrl: '', role: 'researcher', organization: 'Carbon Systems Lab', createdAt: '2024-01-08', lastLoginAt: '2026-09-12' },
  { id: 'inv-noah', name: 'Noah Williams', email: 'noah@terraledger.demo', avatarUrl: '', role: 'investor', organization: 'Northstar Impact', createdAt: '2023-10-22', lastLoginAt: '2026-09-12' }
];
