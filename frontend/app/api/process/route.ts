import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { spawn } from 'child_process';
import { TextEncoder } from 'util';

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
      const target = finalPath || outputPath;
      try {
        await fs.access(target);
        const data = await fs.readFile(target);
        send('done', data.toString('base64'));
      } catch {
        send('error', `File not found: ${target}`);
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
