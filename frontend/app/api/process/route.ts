import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export async function POST(req: Request) {
  const formData = await req.formData();
  const files = formData.getAll('images') as File[];
  if (!files.length) {
    return new NextResponse('No files uploaded', { status: 400 });
  }
  const autoAlign = formData.get('autoAlign') === '1';
  const antiGhost = formData.get('antiGhost') === '1';
  const dir = await fs.mkdtemp(join(tmpdir(), 'hdr-'));
  const paths: string[] = [];
  for (const file of files) {
    const buffer = Buffer.from(await file.arrayBuffer());
    const filePath = join(dir, file.name);
    await fs.writeFile(filePath, buffer);
    paths.push(filePath);
  }
  const outputPath = join(dir, 'result.jpg');
  try {
    const script = join(process.cwd(), '..', 'process_uploads.py');
    const args: string[] = [];
    if (autoAlign) args.push('--align');
    if (antiGhost) args.push('--deghost');
    await execFileAsync('python3', [script, ...args, ...paths, outputPath]);
    const data = await fs.readFile(outputPath);
    return new NextResponse(data, {
      status: 200,
      headers: {
        'Content-Type': 'image/jpeg',
        'Content-Disposition': 'attachment; filename="result.jpg"'
      }
    });
  } catch (err: any) {
    return new NextResponse('Error processing images: ' + err, { status: 500 });
  }
}
