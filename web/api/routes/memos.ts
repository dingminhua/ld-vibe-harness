/**
 * Memos API 路由：备忘速记创建入口（仅 Memo 允许 Web 创建，其他类型由 AI 创建）
 *
 * 依据：
 * - specs/26-Memo-备忘.md §8.3 Web 信息同步
 * - specs/08-Web信息同步实现规范.md §8.2 Web 事实源写入白名单
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { LDVH_BASE_DIR } from '../services/pytools.js'

const router = Router()

const MEMOS_DIR = path.join(LDVH_BASE_DIR, 'memos')
const VALID_PRIORITY = ['P0', 'P1', 'P2', 'P3']
const MEMO_REQUIRED_FIELDS = [
  'id',
  'type',
  'title',
  'status',
  'created',
  'updated',
  'description',
  'source',
  'priority',
  'status_history',
]

/** 生成下一个 memo ID */
function nextMemoId(): string {
  if (!fs.existsSync(MEMOS_DIR)) {
    fs.mkdirSync(MEMOS_DIR, { recursive: true })
  }
  const files = fs.readdirSync(MEMOS_DIR).filter(f => /^memo-\d{4}-/.test(f))
  let maxNum = 0
  for (const f of files) {
    const m = f.match(/^memo-(\d{4})-/)
    if (m) {
      const n = parseInt(m[1], 10)
      if (n > maxNum) maxNum = n
    }
  }
  return `memo-${String(maxNum + 1).padStart(4, '0')}`
}

/** 将 title 转成短横线文件名 */
function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40) || 'memo'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function validatePersistedMemo(data: unknown, expectedId: string): string[] {
  if (!isRecord(data)) {
    return ['persisted memo is not an object']
  }

  const errors: string[] = []
  for (const field of MEMO_REQUIRED_FIELDS) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      errors.push(`${field} is missing`)
    }
  }
  if (data.id !== expectedId) {
    errors.push('id mismatch')
  }
  if (data.type !== 'memo') {
    errors.push('type must be memo')
  }
  if (data.status !== 'pending') {
    errors.push('status must be pending')
  }
  if (!Array.isArray(data.status_history) || data.status_history.length === 0) {
    errors.push('status_history must be a non-empty list')
  }
  return errors
}

router.post('/', (req: Request, res: Response): void => {
  try {
    const { title, description, source, priority } = req.body

    // 校验必填字段
    const errors: string[] = []
    if (!title || typeof title !== 'string' || !title.trim()) {
      errors.push('title is required')
    }
    if (!description || typeof description !== 'string' || !description.trim()) {
      errors.push('description is required')
    }
    if (!source || typeof source !== 'string' || !source.trim()) {
      errors.push('source is required')
    }
    if (!priority || !VALID_PRIORITY.includes(priority)) {
      errors.push(`priority must be one of: ${VALID_PRIORITY.join(', ')}`)
    }

    if (errors.length > 0) {
      res.status(400).json({ ok: false, errors })
      return
    }

    const today = new Date().toISOString().slice(0, 10)
    const id = nextMemoId()
    const slug = slugify(title.trim())
    const filename = `${id}-${slug}.yaml`
    const filePath = path.join(MEMOS_DIR, filename)

    if (fs.existsSync(filePath)) {
      res.status(409).json({
        ok: false,
        code: 'MEMO_FILE_CONFLICT',
        error: `Memo 文件已存在: ${filename}`,
      })
      return
    }

    const memo = {
      id,
      type: 'memo',
      title: title.trim(),
      status: 'pending',
      created: today,
      updated: today,
      description: description.trim(),
      source: source.trim(),
      priority,
      resolved_to: '',
      resolved_at: '',
      discard_reason: '',
      related_workareas: [] as string[],
      related_taskplans: [] as string[],
      related_tasks: [] as string[],
      related_adrs: [] as string[],
      related_changes: [] as string[],
      related_docs: [] as string[],
      status_history: [
        {
          at: today,
          from: 'created',
          to: 'pending',
          actor: 'human',
          reason: '通过 Web 备忘速记入口创建',
        },
      ],
    }

    const yamlText = yaml.dump(memo, { lineWidth: -1, quotingType: '"', forceQuotes: false })
    try {
      fs.writeFileSync(filePath, yamlText, { encoding: 'utf-8', flag: 'wx' })
    } catch (err) {
      const code = (err as NodeJS.ErrnoException).code
      if (code === 'EEXIST') {
        res.status(409).json({
          ok: false,
          code: 'MEMO_FILE_CONFLICT',
          error: `Memo 文件已存在: ${filename}`,
        })
        return
      }
      res.status(500).json({
        ok: false,
        code: 'MEMO_WRITE_FAILED',
        error: err instanceof Error ? err.message : 'Memo 写入失败',
      })
      return
    }

    let persisted: unknown
    try {
      persisted = yaml.load(fs.readFileSync(filePath, 'utf-8'))
    } catch (err) {
      res.status(500).json({
        ok: false,
        code: 'MEMO_WRITE_VERIFY_FAILED',
        error: err instanceof Error ? err.message : 'Memo 写后校验失败',
      })
      return
    }

    const verificationErrors = validatePersistedMemo(persisted, id)
    if (verificationErrors.length > 0) {
      res.status(500).json({
        ok: false,
        code: 'MEMO_WRITE_VERIFY_FAILED',
        errors: verificationErrors,
      })
      return
    }

    res.status(201).json({
      ok: true,
      action: 'create',
      target: filename,
      summary: { id, type: 'memo', status: 'pending' },
      data: memo,
    })
  } catch (err) {
    res.status(500).json({
      ok: false,
      error: err instanceof Error ? err.message : 'Memo 创建失败',
    })
  }
})

export default router
