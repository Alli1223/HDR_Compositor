import { NextResponse } from 'next/server';
import { join } from 'path';
import { promises as fs } from 'fs';

const DAY_MS = 24 * 60 * 60 * 1000;

async function cleanupOldDownloads(dir: string) {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    const now = Date.now();
    await Promise.all(
      entries
        .filter((e) => e.isFile())
        .map(async (e) => {
          const p = join(dir, e.name);
          const stat = await fs.stat(p);
          if (now - stat.mtimeMs > DAY_MS) {
            await fs.unlink(p);
          }
        })
    );
  } catch {
    /* ignore errors */
  }
}

export async function GET(req: Request) {
  const { pathname } = new URL(req.url);
  const file = pathname.split('/').pop() || '';
  const filePath = join(process.cwd(), 'public', 'downloads', file);
  await cleanupOldDownloads(join(process.cwd(), 'public', 'downloads'));
  try {
    const data = await fs.readFile(filePath);
    return new NextResponse(data, {
      headers: {
        'Content-Type': 'image/jpeg',
        'Content-Disposition': `attachment; filename="${file}"`,
      },
    });
  } catch {
    return new NextResponse('Not Found', { status: 404 });
  }
}
