/**
 * Sparks API 路由：火花速记创建入口（仅 Spark 允许 Web 创建，其他类型由 AI 创建）
 *
 * 依据：
 * - specs/20-Spark-火花.md
 * - specs/08-Web信息同步规范.md
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { LDVH_BASE_DIR } from '../services/pytools.js'

const router = Router()

const SPARKS_DIR = path.join(LDVH_BASE_DIR, 'sparks')
const VALID_PRIORITY = ['P0', 'P1', 'P2', 'P3']
const SPARK_REQUIRED_FIELDS = [
  'id',
  'type',
  'title',
  'status',
  'created',
  'updated',
  'description',
  'evolution',
  'source',
  'priority',
  'related_workcases',
  'related_adrs',
  'related_studies',
  'related_docs',
]

/** 生成下一个 spark ID */
function nextSparkId(): string {
  if (!fs.existsSync(SPARKS_DIR)) {
    fs.mkdirSync(SPARKS_DIR, { recursive: true })
  }
  const files = fs.readdirSync(SPARKS_DIR).filter(f => /^spark-\d{4}-/.test(f))
  let maxNum = 0
  for (const f of files) {
    const m = f.match(/^spark-(\d{4})-/)
    if (m) {
      const n = parseInt(m[1], 10)
      if (n > maxNum) maxNum = n
    }
  }
  return `spark-${String(maxNum + 1).padStart(4, '0')}`
}

/** 将 title 转成短横线文件名 */
function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40) || 'spark'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function pad2(value: number): string {
  return String(value).padStart(2, '0')
}

function localIsoTimestamp(date = new Date()): string {
  return [
    date.getFullYear(),
    pad2(date.getMonth() + 1),
    pad2(date.getDate()),
  ].join('-') + `T${pad2(date.getHours())}:${pad2(date.getMinutes())}:${pad2(date.getSeconds())}`
}

function validatePersistedSpark(data: unknown, expectedId: string): string[] {
  if (!isRecord(data)) {
    return ['persisted spark is not an object']
  }

  const errors: string[] = []
  for (const field of SPARK_REQUIRED_FIELDS) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      errors.push(`${field} is missing`)
    }
  }
  if (data.id !== expectedId) {
    errors.push('id mismatch')
  }
  if (data.type !== 'spark') {
    errors.push('type must be spark')
  }
  if (data.status !== 'pending') {
    errors.push('status must be pending')
  }
  if (data.source !== 'web') {
    errors.push('source must be web for Web spark creation')
  }
  for (const field of ['evolution', 'related_workcases', 'related_adrs', 'related_studies', 'related_docs']) {
    if (!Array.isArray(data[field])) {
      errors.push(`${field} must be an array`)
    }
  }
  if ('status_history' in data) {
    errors.push('status_history must not be written by Web spark creation')
  }
  if ('规范10' in data) {
    errors.push('规范10 must not be written by Web spark creation')
  }
  return errors
}

router.post('/', (req: Request, res: Response): void => {
  try {
    const { title, description, priority } = req.body

    // 校验必填字段
    const errors: string[] = []
    if (!title || typeof title !== 'string' || !title.trim()) {
      errors.push('title is required')
    }
    if (!description || typeof description !== 'string' || !description.trim()) {
      errors.push('description is required')
    }
    if (!priority || !VALID_PRIORITY.includes(priority)) {
      errors.push(`priority must be one of: ${VALID_PRIORITY.join(', ')}`)
    }

    if (errors.length > 0) {
      res.status(400).json({ ok: false, errors })
      return
    }

    const now = localIsoTimestamp()
    const id = nextSparkId()
    const slug = slugify(title.trim())
    const filename = `${id}-${slug}.yaml`
    const filePath = path.join(SPARKS_DIR, filename)

    if (fs.existsSync(filePath)) {
      res.status(409).json({
        ok: false,
        code: 'SPARK_FILE_CONFLICT',
        error: `Spark 文件已存在: ${filename}`,
      })
      return
    }

    const spark = {
      id,
      type: 'spark',
      title: title.trim(),
      status: 'pending',
      created: now,
      updated: now,
      description: description.trim(),
      evolution: [] as Array<Record<string, string>>,
      source: 'web',
      source_detail: '',
      priority,
      resolved_to: '',
      resolved_at: '',
      discard_reason: '',
      related_workcases: [] as string[],
      related_adrs: [] as string[],
      related_studies: [] as string[],
      related_docs: [] as string[],
    }

    const yamlText = yaml.dump(spark, { lineWidth: -1, quotingType: '"', forceQuotes: false })
    try {
      fs.writeFileSync(filePath, yamlText, { encoding: 'utf-8', flag: 'wx' })
    } catch (err) {
      const code = (err as NodeJS.ErrnoException).code
      if (code === 'EEXIST') {
        res.status(409).json({
          ok: false,
          code: 'SPARK_FILE_CONFLICT',
          error: `Spark 文件已存在: ${filename}`,
        })
        return
      }
      res.status(500).json({
        ok: false,
        code: 'SPARK_WRITE_FAILED',
        error: err instanceof Error ? err.message : 'Spark 写入失败',
      })
      return
    }

    let persisted: unknown
    try {
      persisted = yaml.load(fs.readFileSync(filePath, 'utf-8'))
    } catch (err) {
      res.status(500).json({
        ok: false,
        code: 'SPARK_WRITE_VERIFY_FAILED',
        error: err instanceof Error ? err.message : 'Spark 写后校验失败',
      })
      return
    }

    const verificationErrors = validatePersistedSpark(persisted, id)
    if (verificationErrors.length > 0) {
      res.status(500).json({
        ok: false,
        code: 'SPARK_WRITE_VERIFY_FAILED',
        errors: verificationErrors,
      })
      return
    }

    res.status(201).json({
      ok: true,
      action: 'create',
      target: filename,
      summary: {
        id,
        type: 'spark',
        status: 'pending',
        source_refs: [{ path: `ldvh-base/sparks/${filename}`, role: 'fact_instance' }],
      },
      data: {
        ...spark,
        path: filePath,
        source_refs: [{ path: `ldvh-base/sparks/${filename}`, role: 'fact_instance' }],
      },
    })
  } catch (err) {
    res.status(500).json({
      ok: false,
      error: err instanceof Error ? err.message : 'Spark 创建失败',
    })
  }
})

export default router
