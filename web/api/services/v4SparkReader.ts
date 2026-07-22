import {
  invokeV4FactsMachine,
  type V4FactsMachineRequest,
  type V4FactsMachineResponse,
  type V4FactsScope,
  type V4FactsTransportOptions,
} from '../internal/v4FactsTransport.js'

export interface V4SparkReaderConfig extends V4FactsTransportOptions {
  scope: V4FactsScope
}

function request(
  operation: V4FactsMachineRequest['operation'],
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

function transport(config: V4SparkReaderConfig): V4FactsTransportOptions {
  return {
    pythonExecutable: config.pythonExecutable,
    timeoutMs: config.timeoutMs,
    spawnProcess: config.spawnProcess,
  }
}

export async function listV4Sparks(config: V4SparkReaderConfig): Promise<V4FactsMachineResponse> {
  return await invokeV4FactsMachine(request('list-sparks', config.scope, {}), transport(config))
}

export async function readV4Spark(
  config: V4SparkReaderConfig,
  objectId: string,
): Promise<V4FactsMachineResponse> {
  return await invokeV4FactsMachine(request('read-spark', config.scope, { object_id: objectId }), transport(config))
}

export async function captureV4Spark(
  config: V4SparkReaderConfig,
  capture: { title: string; intent: string; description: string; priority: string },
): Promise<V4FactsMachineResponse> {
  return await invokeV4FactsMachine(request('create-spark', config.scope, { ...capture }), transport(config))
}
