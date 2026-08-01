import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { after, test } from 'node:test';
import yaml from 'js-yaml';
import {
  FILE_ASSET_PREVIEW_LIMIT_BYTES,
  readFileAssetPreview,
} from '../../api/services/fileAssetPreview.ts';

const roots: string[] = [];

after(async () => {
  await Promise.all(roots.map((root) => rm(root, { recursive: true, force: true })));
});

async function createAsset({
  id,
  mediaType,
  payload,
  status = 'active',
  size = payload.byteLength,
  digest = createHash('sha256').update(payload).digest('hex'),
}: {
  id: string;
  mediaType: string;
  payload: Buffer;
  status?: string;
  size?: number;
  digest?: string;
}) {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-file-preview-'));
  roots.push(root);
  const assetDir = path.join(root, 'ldvh-base', 'file-assets', id);
  await mkdir(assetDir, { recursive: true });
  await writeFile(path.join(assetDir, 'file-asset.yaml'), yaml.dump({
    object_id: id,
    fact_type_key: 'file-asset',
    status,
    filename: `sample.${mediaType === 'text/markdown' ? 'md' : 'bin'}`,
    media_type: mediaType,
    size_bytes: size,
    content_sha256: digest,
  }));
  await writeFile(path.join(assetDir, 'payload'), payload);
  return {
    root,
    assetDir,
    scope: { worktreeLocator: root, governedProjectId: 'test' },
  };
}

test('reads a verified Markdown FileAsset payload', async () => {
  const payload = Buffer.from('# Preview\n\nHello.\n');
  const { scope } = await createAsset({ id: 'file-asset-1001', mediaType: 'text/markdown', payload });
  const result = await readFileAssetPreview(scope, 'file-asset-1001');
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.equal(result.kind, 'markdown');
  assert.equal(result.data.toString('utf8'), payload.toString('utf8'));
});

test('accepts supported raster signatures', async () => {
  const samples = [
    ['image/png', Buffer.from([137, 80, 78, 71, 13, 10, 26, 10, 0])],
    ['image/jpeg', Buffer.from([0xff, 0xd8, 0x00, 0xff, 0xd9])],
    ['image/gif', Buffer.from('GIF89a-body')],
    ['image/webp', Buffer.from('RIFF0000WEBP')],
    ['image/avif', Buffer.from([0, 0, 0, 20, 0x66, 0x74, 0x79, 0x70, 0x61, 0x76, 0x69, 0x66, 0, 0, 0, 0])],
  ] as const;

  for (let index = 0; index < samples.length; index += 1) {
    const [mediaType, payload] = samples[index];
    const id = `file-asset-11${String(index).padStart(2, '0')}`;
    const { scope } = await createAsset({ id, mediaType, payload });
    const result = await readFileAssetPreview(scope, id);
    assert.equal(result.ok, true, mediaType);
    if (result.ok) assert.equal(result.kind, 'image');
  }
});

test('accepts a static SVG and rejects active SVG content', async () => {
  const safe = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="4"/></svg>');
  const safeAsset = await createAsset({ id: 'file-asset-1201', mediaType: 'image/svg+xml', payload: safe });
  assert.equal((await readFileAssetPreview(safeAsset.scope, 'file-asset-1201')).ok, true);

  const unsafe = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>');
  const unsafeAsset = await createAsset({ id: 'file-asset-1202', mediaType: 'image/svg+xml', payload: unsafe });
  const result = await readFileAssetPreview(unsafeAsset.scope, 'file-asset-1202');
  assert.deepEqual(result.ok ? null : result.code, 'unsafe');

  const externalStyle = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"><style>circle{fill:url(https://example.test/a)}</style></svg>');
  const styleAsset = await createAsset({ id: 'file-asset-1203', mediaType: 'image/svg+xml', payload: externalStyle });
  const styleResult = await readFileAssetPreview(styleAsset.scope, 'file-asset-1203');
  assert.deepEqual(styleResult.ok ? null : styleResult.code, 'unsafe');

  const unsafeVariants = [
    '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
    '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.test/a.png"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><div>HTML</div></foreignObject></svg>',
  ];
  for (let index = 0; index < unsafeVariants.length; index += 1) {
    const id = `file-asset-121${index}`;
    const candidate = Buffer.from(unsafeVariants[index]);
    const asset = await createAsset({ id, mediaType: 'image/svg+xml', payload: candidate });
    const candidateResult = await readFileAssetPreview(asset.scope, id);
    assert.deepEqual(candidateResult.ok ? null : candidateResult.code, 'unsafe');
  }
});

test('rejects digest mismatches, unsupported types, deleted assets, and oversized payloads', async () => {
  const mismatch = await createAsset({
    id: 'file-asset-1301',
    mediaType: 'text/markdown',
    payload: Buffer.from('changed'),
    digest: '0'.repeat(64),
  });
  const mismatchResult = await readFileAssetPreview(mismatch.scope, 'file-asset-1301');
  assert.deepEqual(mismatchResult.ok ? null : mismatchResult.code, 'integrity_failed');

  const unsupported = await createAsset({
    id: 'file-asset-1302',
    mediaType: 'application/pdf',
    payload: Buffer.from('%PDF'),
  });
  const unsupportedResult = await readFileAssetPreview(unsupported.scope, 'file-asset-1302');
  assert.deepEqual(unsupportedResult.ok ? null : unsupportedResult.code, 'unsupported');

  const wrongSignature = await createAsset({
    id: 'file-asset-1305',
    mediaType: 'image/png',
    payload: Buffer.from('not a png'),
  });
  const wrongSignatureResult = await readFileAssetPreview(wrongSignature.scope, 'file-asset-1305');
  assert.deepEqual(wrongSignatureResult.ok ? null : wrongSignatureResult.code, 'integrity_failed');

  const deleted = await createAsset({
    id: 'file-asset-1303',
    mediaType: 'text/markdown',
    payload: Buffer.from('deleted'),
    status: 'deleted',
  });
  const deletedResult = await readFileAssetPreview(deleted.scope, 'file-asset-1303');
  assert.deepEqual(deletedResult.ok ? null : deletedResult.code, 'unavailable');

  const oversizedPayload = Buffer.alloc(FILE_ASSET_PREVIEW_LIMIT_BYTES + 1, 0x20);
  const oversized = await createAsset({
    id: 'file-asset-1304',
    mediaType: 'text/markdown',
    payload: oversizedPayload,
  });
  const oversizedResult = await readFileAssetPreview(oversized.scope, 'file-asset-1304');
  assert.deepEqual(oversizedResult.ok ? null : oversizedResult.code, 'too_large');
});

test('accepts the exact 4 MiB boundary and reports a missing object without payload', async () => {
  const boundaryPayload = Buffer.alloc(FILE_ASSET_PREVIEW_LIMIT_BYTES, 0x20);
  const boundary = await createAsset({
    id: 'file-asset-1350',
    mediaType: 'text/markdown',
    payload: boundaryPayload,
  });
  const boundaryResult = await readFileAssetPreview(boundary.scope, 'file-asset-1350');
  assert.equal(boundaryResult.ok, true);

  const missingResult = await readFileAssetPreview(boundary.scope, 'file-asset-9999');
  assert.deepEqual(missingResult.ok ? null : missingResult.code, 'not_found');
  if (!missingResult.ok) assert.equal('data' in missingResult, false);
});

test('refuses a payload symlink', async () => {
  const payload = Buffer.from('outside');
  const asset = await createAsset({ id: 'file-asset-1401', mediaType: 'text/markdown', payload });
  const payloadPath = path.join(asset.assetDir, 'payload');
  const outsidePath = path.join(asset.root, 'outside.md');
  await rm(payloadPath);
  await writeFile(outsidePath, payload);
  await symlink(outsidePath, payloadPath);
  const result = await readFileAssetPreview(asset.scope, 'file-asset-1401');
  assert.deepEqual(result.ok ? null : result.code, 'unavailable');
});
