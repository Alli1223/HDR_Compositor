import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { spawn } from 'child_process';
import { TextEncoder } from 'util';
import { randomUUID } from 'crypto';

export async function POST(req: Request) {
  const formData = await req.formData();
  const files = formData.getAll('images') as File[];
  if (!files.length) {
    return new NextResponse('No files uploaded', { status: 400 });
  }
  const autoAlign = formData.get('autoAlign') === '1';
  const antiGhost = formData.get('antiGhost') === '1';
  const contrast = formData.get('contrast');
  const saturation = formData.get('saturation');
  const dir = await fs.mkdtemp(join(tmpdir(), 'hdr-'));
  const paths: string[] = [];
  for (const file of files) {
    const buffer = Buffer.from(await file.arrayBuffer());
    const filePath = join(dir, file.name);
    await fs.writeFile(filePath, buffer);
    paths.push(filePath);
  }
  const outputPath = join(dir, 'result.jpg');
  // Final images will be moved to the public downloads directory so they can
  // be retrieved later via a normal HTTP request.
  // Use the Next.js public directory so files can be served statically. Since
  // this API route executes within the `frontend` directory we don't prefix
  // the path with another `frontend` segment.
  const downloadsDir = join(process.cwd(), 'public', 'downloads');
  await fs.mkdir(downloadsDir, { recursive: true });
  const fileId = `${randomUUID()}.jpg`;
  const finalDownloadPath = join(downloadsDir, fileId);
  const script = join(process.cwd(), '..', 'process_uploads.py');
  const args: string[] = [];
  if (autoAlign) args.push('--align');
  if (antiGhost) args.push('--deghost');
  if (contrast) args.push('--contrast', String(contrast));
  if (saturation) args.push('--saturation', String(saturation));

  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const enc = new TextEncoder();

  const send = (event: string, data: string) => {
    writer.write(enc.encode(`event: ${event}\ndata: ${data}\n\n`));
  };

  try {
    const child = spawn('python3', [script, ...args, ...paths, outputPath]);
    let finalPath = '';

    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (chunk: string) => {
      chunk.split(/\r?\n/).forEach((line) => {
        if (!line) return;
        if (line.startsWith('PROGRESS')) {
          const pct = line.split(' ')[1];
          send('progress', pct);
        } else {
          finalPath = line.trim();
        }
      });
    });

    child.stderr.on('data', (d) => {
      send('error', d.toString());
    });

    child.on('close', async () => {
      try {
        const src = finalPath || outputPath;
        // Copy the file instead of renaming to avoid issues when the temporary
        // directory lives on a different filesystem than the downloads folder.
        await fs.copyFile(src, finalDownloadPath);
        await fs.unlink(src);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        send('done', `${basePath}/api/downloads/${fileId}`);
      } catch (err: any) {
        send('error', String(err));
      } finally {
        writer.close();
      }
    });
  } catch (err: any) {
    send('error', String(err));
    writer.close();
  }

  return new NextResponse(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    }
  });
}
