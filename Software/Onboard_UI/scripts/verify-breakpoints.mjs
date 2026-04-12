import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = process.cwd();

const checks = [
	{
		name: 'layout includes width and height breakpoint toggles',
		file: 'src/routes/+layout.svelte',
		patterns: ['window.innerWidth <= 640', 'window.innerHeight <= 420', 'hud-breakpoint-width-640', 'hud-breakpoint-height-420']
	},
	{
		name: 'global stylesheet has compact breakpoint media query',
		file: 'src/app.css',
		patterns: ['@media (max-width: 640px), (max-height: 420px)']
	},
	{
		name: 'global stylesheet has class-based fallback breakpoint selectors',
		file: 'src/app.css',
		patterns: ['body.hud-breakpoint-width-640 .hud-grid-3', 'body.hud-breakpoint-height-420 .hud-grid-3']
	}
];

const routeFiles = ['src/routes/+page.svelte', 'src/routes/Navigation/+page.svelte', 'src/routes/Teleprompter/+page.svelte', 'src/routes/Messages/+page.svelte', 'src/routes/Debug/+page.svelte'];

let failed = false;

for (const check of checks) {
	const content = readFileSync(resolve(root, check.file), 'utf8');
	const missing = check.patterns.filter((pattern) => !content.includes(pattern));
	if (missing.length > 0) {
		failed = true;
		console.error(`✗ ${check.name} (${check.file})`);
		for (const pattern of missing) {
			console.error(`  missing: ${pattern}`);
		}
	} else {
		console.log(`✓ ${check.name}`);
	}
}

for (const routeFile of routeFiles) {
	const content = readFileSync(resolve(root, routeFile), 'utf8');
	if (!content.includes('<HudScaffold')) {
		failed = true;
		console.error(`✗ route missing HudScaffold: ${routeFile}`);
	} else {
		console.log(`✓ route breakpoint-ready scaffold: ${routeFile}`);
	}
}

if (failed) {
	process.exit(1);
}
