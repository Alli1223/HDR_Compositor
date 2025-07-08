import { NextResponse } from 'next/server';
import { join } from 'path';
import { promises as fs } from 'fs';

export async function GET(req: Request) {
  const { pathname } = new URL(req.url);
  const file = pathname.split('/').pop() || '';
  const filePath = join(process.cwd(), 'public', 'downloads', file);
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
