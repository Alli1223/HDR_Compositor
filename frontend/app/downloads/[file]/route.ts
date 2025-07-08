import { NextRequest, NextResponse } from 'next/server';
import { join } from 'path';
import { promises as fs } from 'fs';

export async function GET(req: NextRequest, { params }: { params: { file: string } }) {
  try {
    const filePath = join(process.cwd(), 'public', 'downloads', params.file);
    const data = await fs.readFile(filePath);
    return new NextResponse(data, {
      headers: { 'Content-Type': 'image/jpeg' }
    });
  } catch (err) {
    return new NextResponse('Not Found', { status: 404 });
  }
}
