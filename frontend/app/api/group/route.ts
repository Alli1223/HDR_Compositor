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
  const dir = await fs.mkdtemp(join(tmpdir(), 'hdr-group-'));
  const paths: string[] = [];
  for (const file of files) {
    const buffer = Buffer.from(await file.arrayBuffer());
    const filePath = join(dir, file.name);
    await fs.writeFile(filePath, buffer);
    paths.push(filePath);
  }
  try {
    const script = join(process.cwd(), '..', 'group_uploads.py');
    const { stdout } = await execFileAsync('python3', [script, ...paths]);
    return NextResponse.json(JSON.parse(stdout));
  } catch (err: any) {
    return new NextResponse('Error grouping images: ' + err, { status: 500 });
  }
}
