export interface Theme {
  mode: 'dark' | 'light';
  bg: string;
  surface: string;
  surfaceHi: string;
  border: string;
  borderHi: string;
  text: string;
  muted: string;
  dim: string;
  accent: string;
  accentDim: string;
  green: string;
  greenDim: string;
  amber: string;
  amberDim: string;
  red: string;
  redDim: string;
  purple: string;
  inputBg: string;
  codeBg: string;
  navBg: string;
  cardShadow: string;
  scrollThumb: string;
}

export const DARK: Theme = {
  mode: 'dark',
  bg: '#07111f',
  surface: '#0c1825',
  surfaceHi: '#111f30',
  border: '#152030',
  borderHi: '#1e3248',
  text: '#ddeaf7',
  muted: '#517898',
  dim: '#2a4361',
  accent: '#4b7dff',
  accentDim: 'rgba(75,125,255,0.12)',
  green: '#1fd49e',
  greenDim: 'rgba(31,212,158,0.10)',
  amber: '#f2a020',
  amberDim: 'rgba(242,160,32,0.10)',
  red: '#ef5060',
  redDim: 'rgba(239,80,96,0.10)',
  purple: '#a78bfa',
  inputBg: '#060e1a',
  codeBg: '#060e1a',
  navBg: 'rgba(7,17,31,0.92)',
  cardShadow: '0 8px 32px rgba(0,0,0,0.5)',
  scrollThumb: '#1e3248',
};

export const LIGHT: Theme = {
  mode: 'light',
  bg: '#f0f4f9',
  surface: '#ffffff',
  surfaceHi: '#f5f8fc',
  border: '#dde5ef',
  borderHi: '#c8d5e6',
  text: '#0e1d30',
  muted: '#5a7a99',
  dim: '#9aaec4',
  accent: '#2a5de8',
  accentDim: 'rgba(42,93,232,0.09)',
  green: '#0fa878',
  greenDim: 'rgba(15,168,120,0.09)',
  amber: '#c07800',
  amberDim: 'rgba(192,120,0,0.09)',
  red: '#d63040',
  redDim: 'rgba(214,48,64,0.09)',
  purple: '#6d4fd4',
  inputBg: '#f0f4f9',
  codeBg: '#e8edf5',
  navBg: 'rgba(240,244,249,0.94)',
  cardShadow: '0 4px 20px rgba(0,0,0,0.08)',
  scrollThumb: '#c8d5e6',
};

export const INSTALL_COLORS: Record<string, string> = {
  'claude-code': '#4b7dff',
  'mcp': '#1fd49e',
  'manual': '#f2a020',
};
