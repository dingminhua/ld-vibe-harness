import path from 'node:path'

import type { V4FactReaderConfig } from './v4FactReader.js'
import type { V4SparkReaderConfig } from './v4SparkReader.js'

export class V4FactsConfigurationError extends Error {
  readonly code = 'v4_facts_unavailable'

  constructor(message: string) {
    super(message)
    this.name = 'V4FactsConfigurationError'
  }
}

function required(name: string): string {
  const value = process.env[name]
  if (!value) throw new V4FactsConfigurationError(`${name} must be configured for V4 Web facts`)
  if (!path.isAbsolute(value)) throw new V4FactsConfigurationError(`${name} must be an absolute path`)
  return value
}

function requiredProjectId(): string {
  const value = process.env.LDVH_WEB_GOVERNED_PROJECT_ID
  if (!value) throw new V4FactsConfigurationError('LDVH_WEB_GOVERNED_PROJECT_ID must be configured for V4 Web facts')
  return value
}

export function v4FactReaderConfig(): V4FactReaderConfig {
  return {
    pythonExecutable: required('LDVH_WEB_PYTHON'),
    scope: {
      workspace_root: required('LDVH_WEB_WORKSPACE_ROOT'),
      worktree_locator: required('LDVH_WEB_WORKTREE_LOCATOR'),
      expected_governed_project_id: requiredProjectId(),
    },
  }
}

export function v4SparkReaderConfig(): V4SparkReaderConfig {
  return v4FactReaderConfig()
}
