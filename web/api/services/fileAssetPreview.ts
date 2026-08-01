import { constants } from 'node:fs'
import type { BigIntStats } from 'node:fs'
import { lstat, open, readdir } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import path from 'node:path'
import yaml from 'js-yaml'
import type { LocalFactScope } from './localFactReader.js'

export const FILE_ASSET_PREVIEW_LIMIT_BYTES = 4 * 1024 * 1024

export type FileAssetPreviewFailureCode =
  | 'not_found'
  | 'unavailable'
  | 'integrity_failed'
  | 'unsupported'
  | 'unsafe'
  | 'too_large'

export type FileAssetPreviewResult =
  | {
      ok: true
      data: Buffer
      filename: string
      mediaType: string
      kind: 'markdown' | 'image'
    }
  | {
      ok: false
      code: FileAssetPreviewFailureCode
      message: string
    }

const SUPPORTED_IMAGE_TYPES = new Set([
  'image/svg+xml',
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'image/avif',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function failure(code: FileAssetPreviewFailureCode, message: string): FileAssetPreviewResult {
  return { ok: false, code, message }
}

function isSameIdentity(
  left: BigIntStats,
  right: BigIntStats,
): boolean {
  return left.dev === right.dev
    && left.ino === right.ino
    && left.size === right.size
    && left.mtimeNs === right.mtimeNs
}

async function readNoFollow(filePath: string): Promise<{ data: Buffer; stat: BigIntStats }> {
  const handle = await open(filePath, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0))
  try {
    const before = await handle.stat({ bigint: true })
    if (!before.isFile()) throw new Error('not_an_ordinary_file')
    const data = await handle.readFile()
    const after = await handle.stat({ bigint: true })
    if (!isSameIdentity(before, after) || BigInt(data.byteLength) !== after.size) {
      throw new Error('file_changed_while_reading')
    }
    return { data, stat: after }
  } finally {
    await handle.close()
  }
}

function decodeUtf8(data: Buffer): string | null {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(data)
  } catch {
    return null
  }
}

function hasImageSignature(mediaType: string, data: Buffer): boolean {
  if (mediaType === 'image/png') {
    return data.length >= 8 && data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
  }
  if (mediaType === 'image/jpeg') {
    return data.length >= 4 && data[0] === 0xff && data[1] === 0xd8
      && data[data.length - 2] === 0xff && data[data.length - 1] === 0xd9
  }
  if (mediaType === 'image/gif') {
    const signature = data.subarray(0, 6).toString('ascii')
    return signature === 'GIF87a' || signature === 'GIF89a'
  }
  if (mediaType === 'image/webp') {
    return data.length >= 12
      && data.subarray(0, 4).toString('ascii') === 'RIFF'
      && data.subarray(8, 12).toString('ascii') === 'WEBP'
  }
  if (mediaType === 'image/avif') {
    if (data.length < 16 || data.subarray(4, 8).toString('ascii') !== 'ftyp') return false
    const brands = data.subarray(8, Math.min(data.length, 32)).toString('ascii')
    return brands.includes('avif') || brands.includes('avis')
  }
  return false
}

function isSafeSvg(source: string): boolean {
  if (!/^\s*(?:<\?xml\b[^>]*>\s*)?(?:<!--[^]*?-->\s*)*<svg\b/i.test(source)) return false
  return !/(?:<\s*(?:script|style|foreignObject|iframe|object|embed|audio|video|use)\b|\bon[a-z]+\s*=|\bstyle\s*=|\b(?:href|xlink:href)\s*=|\burl\s*\(|<!DOCTYPE|<!ENTITY)/i.test(source)
}

function validatePayload(mediaType: string, data: Buffer): FileAssetPreviewResult | null {
  if (mediaType === 'text/markdown') {
    return decodeUtf8(data) === null ? failure('unsafe', 'Markdown 内容不是有效 UTF-8') : null
  }
  if (mediaType === 'image/svg+xml') {
    const source = decodeUtf8(data)
    return source !== null && isSafeSvg(source)
      ? null
      : failure('unsafe', 'SVG 包含不可安全预览的结构')
  }
  if (SUPPORTED_IMAGE_TYPES.has(mediaType)) {
    return hasImageSignature(mediaType, data)
      ? null
      : failure('integrity_failed', '文件内容与声明的媒体类型不一致')
  }
  return failure('unsupported', `暂不支持预览 ${mediaType || '未知媒体类型'}`)
}

export async function readFileAssetPreview(scope: LocalFactScope, objectId: string): Promise<FileAssetPreviewResult> {
  if (!/^file-asset-\d{4,}$/.test(objectId)) return failure('not_found', '文件对象不存在')

  const assetDir = path.join(scope.worktreeLocator, 'ldvh-base', 'file-assets', objectId)
  const manifestPath = path.join(assetDir, 'file-asset.yaml')
  const payloadPath = path.join(assetDir, 'payload')

  try {
    const directoryBefore = await lstat(assetDir, { bigint: true })
    if (!directoryBefore.isDirectory() || directoryBefore.isSymbolicLink()) {
      return failure('unavailable', '文件对象载体不可读取')
    }

    const members = await readdir(assetDir, { withFileTypes: true })
    if (members.length !== 2
      || !members.every((member) => member.isFile())
      || !members.some((member) => member.name === 'file-asset.yaml')
      || !members.some((member) => member.name === 'payload')) {
      return failure('unavailable', '文件对象载体结构不完整')
    }

    const manifestBefore = await readNoFollow(manifestPath)
    const parsed = yaml.load(manifestBefore.data.toString('utf8'))
    if (!isRecord(parsed)
      || parsed.object_id !== objectId
      || parsed.fact_type_key !== 'file-asset'
      || parsed.status !== 'active'
      || typeof parsed.filename !== 'string'
      || typeof parsed.media_type !== 'string'
      || typeof parsed.size_bytes !== 'number'
      || typeof parsed.content_sha256 !== 'string') {
      return failure('unavailable', '文件对象清单不可用于预览')
    }
    if (parsed.size_bytes > FILE_ASSET_PREVIEW_LIMIT_BYTES) {
      return failure('too_large', '文件超过 4 MiB 预览上限')
    }

    const payload = await readNoFollow(payloadPath)
    if (payload.data.byteLength > FILE_ASSET_PREVIEW_LIMIT_BYTES) {
      return failure('too_large', '文件超过 4 MiB 预览上限')
    }
    const digest = createHash('sha256').update(payload.data).digest('hex')
    if (payload.data.byteLength !== parsed.size_bytes || digest !== parsed.content_sha256.toLowerCase()) {
      return failure('integrity_failed', '文件大小或内容摘要与清单不一致')
    }

    const validationFailure = validatePayload(parsed.media_type, payload.data)
    if (validationFailure) return validationFailure

    const manifestAfter = await readNoFollow(manifestPath)
    const directoryAfter = await lstat(assetDir, { bigint: true })
    if (!isSameIdentity(manifestBefore.stat, manifestAfter.stat)
      || !manifestBefore.data.equals(manifestAfter.data)
      || !isSameIdentity(directoryBefore, directoryAfter)) {
      return failure('unavailable', '文件对象在读取期间发生变化')
    }

    return {
      ok: true,
      data: payload.data,
      filename: parsed.filename,
      mediaType: parsed.media_type,
      kind: parsed.media_type === 'text/markdown' ? 'markdown' : 'image',
    }
  } catch (error) {
    const code = (error as NodeJS.ErrnoException)?.code
    if (code === 'ENOENT' || code === 'ENOTDIR') return failure('not_found', '文件对象或正文不存在')
    return failure('unavailable', '文件正文当前不可安全读取')
  }
}
