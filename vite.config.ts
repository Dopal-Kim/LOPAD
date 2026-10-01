import { createReadStream, cpSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';

/**
 * 아트·음향 산출물 서빙 (계약 contracts/art-assets.md §4, 음향은 assets/audio/manifest.json 계약 초안).
 * `assets/**` 는 Vite 의 publicDir(`public/`) 이 아니므로 별도 플러그인으로
 *  - dev: `/assets-game/<경로>` 요청을 `assets/<경로>` 파일로 응답
 *  - build: `assets/**` 를 `dist/assets-game/**` 로 복사
 *  - 양쪽 모두 `assets-game/manifest.json` (존재하는 파일 목록) 을 제공해 로더가 404 없이 선택적으로 로드한다.
 * 해시 번들 폴더 `dist/assets/` 와 겹치지 않도록 `assets-game` 을 쓴다. base 가 './' 이므로 상대 경로로 동작한다.
 */
const GAME_ASSET_DIR = 'assets';
const GAME_ASSET_URL = '/assets-game/';
const MANIFEST = 'manifest.json';
const MIME: Record<string, string> = {
  png: 'image/png',
  json: 'application/json',
  ogg: 'audio/ogg',
  mp3: 'audio/mpeg',
  wav: 'audio/wav',
};

function listFiles(dir: string, base = dir): string[] {
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(full, base));
    else if (entry.isFile()) out.push(relative(base, full).split('\\').join('/'));
  }
  return out.sort();
}

function gameAssets(): Plugin {
  let root = process.cwd();
  let outDir = 'dist';
  return {
    name: 'lopad-game-assets',
    configResolved(config) {
      root = config.root;
      outDir = config.build.outDir;
    },
    configureServer(server) {
      const srcDir = resolve(root, GAME_ASSET_DIR);
      server.middlewares.use((req, res, next) => {
        const url = req.url ?? '';
        if (!url.startsWith(GAME_ASSET_URL)) return next();
        const rel = decodeURIComponent(url.slice(GAME_ASSET_URL.length).split('?')[0]);
        if (rel === MANIFEST) {
          res.setHeader('Content-Type', MIME.json);
          res.end(JSON.stringify({ files: listFiles(srcDir) }));
          return;
        }
        const file = resolve(srcDir, rel);
        if (!file.startsWith(srcDir) || !existsSync(file) || !statSync(file).isFile()) {
          res.statusCode = 404;
          res.end();
          return;
        }
        res.setHeader('Content-Type', MIME[file.split('.').pop() ?? ''] ?? 'application/octet-stream');
        createReadStream(file).pipe(res);
      });
    },
    closeBundle() {
      const srcDir = resolve(root, GAME_ASSET_DIR);
      const dest = resolve(root, outDir, GAME_ASSET_URL.replace(/\//g, ''));
      mkdirSync(dest, { recursive: true });
      if (existsSync(srcDir)) cpSync(srcDir, dest, { recursive: true });
      writeFileSync(join(dest, MANIFEST), JSON.stringify({ files: listFiles(srcDir) }));
    },
  };
}

// LOPAD build config. Phaser is split into its own chunk so game code rebuilds stay small.
export default defineConfig({
  base: './',
  server: { port: 8080 },
  plugins: [gameAssets()],
  build: {
    rollupOptions: {
      output: { manualChunks: { phaser: ['phaser'] } },
    },
  },
});
