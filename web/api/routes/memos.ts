/**
 * Memos API 路由：备忘速记创建入口（仅 Memo 允许 Web 创建，其他类型由 AI 创建）
 *
 * 依据：
 * - docs/specs/25-Memo-备忘.md §8.3 Web 信息同步
 * - docs/specs/08-Web信息同步实现规范.md §8.2 Web 事实源写入白名单
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { LDVH_BASE_DIR } from '../services/pytools.js'

const router = Router()

const MEMOS_DIR = path.join(LDVH_BASE_DIR, 'memos')
const VALID_CATEGORIES = ['discovery', 'reminder', 'question', 'gap', 'preference']
const VALID_PRIORITIES = ['low', 'medium', 'high']

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
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40) || 'untitled'
}

router.post('/', (req: Request, res: Response): void => {
  try {
    const { title, description, source, category, priority } = req.body

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
    if (!category || !VALID_CATEGORIES.includes(category)) {
      errors.push(`category must be one of: ${VALID_CATEGORIES.join(', ')}`)
    }

    if (errors.length > 0) {
      res.status(400).json({ ok: false, errors })
      return
    }

    const p = priority && VALID_PRIORITIES.includes(priority) ? priority : 'low'
    const today = new Date().toISOString().slice(0, 10)
    const id = nextMemoId()
    const slug = slugify(title.trim())
    const filename = `${id}-${slug}.yaml`
    const filePath = path.join(MEMOS_DIR, filename)

    const memo = {
      id,
      type: 'memo',
      title: title.trim(),
      status: 'draft',
      created: today,
      updated: today,
      description: description.trim(),
      source: source.trim(),
      category,
      priority: p,
      resolved_to: '',
      resolved_at: '',
      archive_reason: '',
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
          to: 'draft',
          actor: 'human',
          reason: '通过 Web 备忘速记入口创建',
        },
      ],
    }

    fs.writeFileSync(
      filePath,
      yaml.dump(memo, { lineWidth: -1, quotingType: '"', forceQuotes: false }),
      'utf-8',
    )

    res.status(201).json({
      ok: true,
      action: 'create',
      target: filename,
      summary: { id, type: 'memo', status: 'draft' },
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
