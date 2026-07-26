import {
  invokeV4FactsMachine,
  type V4FactsMachineRequest,
  type V4FactsMachineResponse,
  type V4FactsOperation,
  type V4FactsScope,
  type V4FactsTransportOptions,
} from '../internal/v4FactsTransport.js'

export type V4MachineFactType = 'spark' | 'workcase'

export interface V4FactReaderConfig extends V4FactsTransportOptions {
  scope: V4FactsScope
}

interface FactOperations {
  list: V4FactsOperation
  read: V4FactsOperation
}

const FACT_OPERATIONS: Record<V4MachineFactType, FactOperations> = {
  spark: { list: 'list-sparks', read: 'read-spark' },
  workcase: { list: 'list-workcases', read: 'read-workcase' },
}

function request(
  operation: V4FactsOperation,
  scope: V4FactsScope,
  args: Record<string, unknown>,
): V4FactsMachineRequest {
  return {
    protocol_version: 1,
    operation,
    scope,
    arguments: args,
  }
}

function transport(config: V4FactReaderConfig): V4FactsTransportOptions {
  return {
    pythonExecutable: config.pythonExecutable,
    timeoutMs: config.timeoutMs,
    spawnProcess: config.spawnProcess,
  }
}

export async function listV4Facts(
  config: V4FactReaderConfig,
  factType: V4MachineFactType,
): Promise<V4FactsMachineResponse> {
  return await invokeV4FactsMachine(
    request(FACT_OPERATIONS[factType].list, config.scope, {}),
    transport(config),
  )
}

export async function readV4Fact(
  config: V4FactReaderConfig,
  factType: V4MachineFactType,
  objectId: string,
): Promise<V4FactsMachineResponse> {
  return await invokeV4FactsMachine(
    request(FACT_OPERATIONS[factType].read, config.scope, { object_id: objectId }),
    transport(config),
  )
}

export async function listV4Sparks(config: V4FactReaderConfig): Promise<V4FactsMachineResponse> {
  return await listV4Facts(config, 'spark')
}

export async function readV4Spark(
  config: V4FactReaderConfig,
  objectId: string,
): Promise<V4FactsMachineResponse> {
  return await readV4Fact(config, 'spark', objectId)
}

export async function listV4WorkCases(config: V4FactReaderConfig): Promise<V4FactsMachineResponse> {
  return await listV4Facts(config, 'workcase')
}

export async function readV4WorkCase(
  config: V4FactReaderConfig,
  objectId: string,
): Promise<V4FactsMachineResponse> {
  return await readV4Fact(config, 'workcase', objectId)
}
