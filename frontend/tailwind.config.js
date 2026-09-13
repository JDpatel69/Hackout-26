/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { role: { farm: '#22c55e', verifier: '#3b82f6', researcher: '#8b5cf6', investor: '#eab308' } } } }
};
