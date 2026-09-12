export const delay = (min = 300, max = 800) => new Promise<void>((resolve) => window.setTimeout(resolve, min + Math.random() * (max - min)));
export const simulateError = (chance = 0.05) => { if (Math.random() < chance) throw new Error('A temporary service issue occurred. Please try again.'); };
export const uid = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
