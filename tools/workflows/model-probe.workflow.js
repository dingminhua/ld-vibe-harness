/*
 * model-probe.workflow.js — DSH workflow 脚本（可复用）
 *
 * 用法：让 AI 调用 workflow 工具，把本文件内容作为 `script` 参数提交，
 * meta 建议为 { name: "model-probe", description: "用指定模型跑探针/任务并返回结果" }。
 *
 * args:
 *   targets: 可选。要探测的模型列表；每项为 "provider/model" 字符串或
 *            { provider, model } 对象。缺省 = 探测下方 CATALOG 全部模型。
 *   prompt:  可选。子代理任务；缺省为连通性自报家门探针。
 *
 * 返回：{ ok, summary, results: [{ target, displayName, available, reply }] }
 * 其中 available=false 表示该 provider/model 路由无法启动子代理（不可用/未配置）。
 *
 * 注意：provider 必须是当前 DSH 实例 LLM seam 中实际注册的路由名。
 * 本机（~/.dsh/settings.yaml）可用的路由见 CATALOG；pi-ai 的 catalog 名
 * "deepseek" 在本机未配置路由，不可用 —— 请用 "deepseek-official"。
 */

const CATALOG = {
  'deepseek-official': {
    displayName: 'DeepSeek 官方（dsh-llm-deepseek）',
    defaultModel: 'deepseek-v4-flash',
    models: ['deepseek-v4-flash', 'deepseek-v4-pro'],
  },
  aixforge: {
    displayName: 'Aixforge（pi-ai，openai-responses）',
    defaultModel: 'glm-5.2',
    models: ['glm-5.2'],
  },
  kimi: {
    displayName: 'Kimi 中转（pi-ai，openai-completions）',
    defaultModel: 'glm-5.3',
    models: ['glm-5.3', 'qwen3.8-max', 'kimi-k3'],
  },
};

const DEFAULT_PROBE_PROMPT =
  '你是一个连通性探针。请只用一句话回答：你当前运行在哪个 provider 和哪个模型上（格式如 provider=deepseek-official, model=deepseek-v4-flash）。不要调用任何工具。';

// ---- 解析目标列表 ----
function parseTargets(raw) {
  const list = Array.isArray(raw) ? raw : raw ? [raw] : null;
  if (!list || list.length === 0) {
    const all = [];
    for (const [provider, info] of Object.entries(CATALOG)) {
      for (const model of info.models) all.push({ provider, model });
    }
    return { targets: all, invalid: [] };
  }
  const targets = [];
  const invalid = [];
  for (const item of list) {
    let provider, model;
    if (typeof item === 'string') {
      const parts = item.split('/');
      provider = parts[0];
      model = parts[1] || null;
    } else if (item && typeof item === 'object') {
      provider = item.provider;
      model = item.model || null;
    }
    if (!provider || !CATALOG[provider]) {
      invalid.push({ provider: provider || null, model: model || null, reason: '未知 provider' });
      continue;
    }
    if (!model) model = CATALOG[provider].defaultModel;
    if (!CATALOG[provider].models.includes(model)) {
      invalid.push({ provider, model, reason: '该 provider 未配置此模型' });
      continue;
    }
    targets.push({ provider, model });
  }
  return { targets, invalid };
}

const { targets, invalid } = parseTargets(args && args.targets);
if (invalid.length > 0) {
  return { ok: false, error: '目标模型不在可用清单内', invalid, catalog: CATALOG };
}
if (targets.length === 0) {
  return { ok: false, error: '没有可探测的目标', catalog: CATALOG };
}

const probePrompt = (args && args.prompt) || DEFAULT_PROBE_PROMPT;

// ---- 探测 ----
phase('Model availability');
const results = await parallel(
  targets.map((t) => async () => {
    const key = `${t.provider}/${t.model}`;
    log(`probing ${key}`);
    const reply = await agent(probePrompt, {
      label: key,
      phase: 'Model availability',
      provider: t.provider,
      model: t.model,
    });
    return {
      target: key,
      displayName: CATALOG[t.provider].displayName,
      available: reply !== null,
      reply: reply === null ? null : String(reply).slice(0, 500),
    };
  })
);

const available = results.filter((r) => r.available);
const summary = `probed ${results.length} targets, ${available.length} available: ${available.map((r) => r.target).join(', ') || '(none)'}`;
log(summary);
return { ok: true, summary, results };
