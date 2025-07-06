export type Hash = string;

export async function computeHash(file: File): Promise<Hash> {
  const img = document.createElement('img');
  const url = URL.createObjectURL(file);
  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = url;
  });
  const canvas = document.createElement('canvas');
  canvas.width = 8;
  canvas.height = 8;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    URL.revokeObjectURL(url);
    return '';
  }
  ctx.drawImage(img, 0, 0, 8, 8);
  const { data } = ctx.getImageData(0, 0, 8, 8);
  const grays: number[] = [];
  for (let i = 0; i < 64; i++) {
    const off = i * 4;
    const r = data[off];
    const g = data[off + 1];
    const b = data[off + 2];
    grays[i] = (r + g + b) / 3;
  }
  const avg = grays.reduce((a, b) => a + b, 0) / grays.length;
  const bits = grays.map((v) => (v > avg ? '1' : '0')).join('');
  URL.revokeObjectURL(url);
  return bits;
}

export function hamming(a: Hash, b: Hash): number {
  const len = Math.min(a.length, b.length);
  let dist = 0;
  for (let i = 0; i < len; i++) {
    if (a[i] !== b[i]) dist++;
  }
  return dist + Math.abs(a.length - b.length);
}
