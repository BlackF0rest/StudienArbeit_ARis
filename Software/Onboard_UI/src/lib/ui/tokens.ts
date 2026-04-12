export const hudTokens = {
	font: {
		stack: "'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
		mono: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
	},
	density: {
		compactClass: 'compact',
		contentPadding: '0.5rem 0.8rem',
		sectionGap: '0.7rem'
	},
	spacing: {
		xs: '0.25rem',
		sm: '0.5rem',
		md: '0.8rem',
		lg: '1rem'
	},
	fontSize: {
		xs: '0.78rem',
		sm: '0.9rem',
		base: '1rem',
		lg: '1.1rem'
	},
	colors: {
		bg: '#000000',
		surface: '#090909',
		surfaceAlt: '#111111',
		text: '#f1fff1',
		muted: '#a6c1a6',
		accent: '#9eff9e',
		accentWeak: '#2f5a2f',
		danger: '#ff8b8b',
		info: '#8bb5ff'
	},
	border: {
		radius: '8px',
		subtle: '1px solid #2f2f2f',
		accent: '1px solid #2f5a2f',
		focus: '1px dashed #2fff44'
	}
} as const;

export type HudTokens = typeof hudTokens;
