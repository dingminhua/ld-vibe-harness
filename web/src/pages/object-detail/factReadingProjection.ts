export type ReferenceRole = 'source' | 'evidence' | 'relation-source' | 'governance';
export type MaterialCategory = 'project' | 'external' | 'unresolved';

export type ReadingMaterial = {
  originPath: string;
  role: ReferenceRole;
  category: MaterialCategory;
  kind: string;
  locator: string;
  version?: string;
  observedAt?: string;
};

export type ReadingRelation = {
  originPath: string;
  relationKey: string;
  target: {
    governedProjectId: string;
    factTypeKey: string;
    objectId: string;
    governanceRefs: ReadingMaterial[];
  };
  sourceRefs: ReadingMaterial[];
};

export type UnresolvedAssociation = {
  originPath: string;
  role: ReferenceRole | 'relation';
  value: unknown;
};

export type FactReadingAssociations = {
  relations: ReadingRelation[];
  projectMaterials: ReadingMaterial[];
  externalInputs: ReadingMaterial[];
  evidenceMaterials: ReadingMaterial[];
  unresolved: UnresolvedAssociation[];
};

const PROJECT_REFERENCE_KINDS = new Set([
  'fact-object',
  'git-revision',
  'repository-path',
  'working-tree',
  'working_tree',
]);

const EXTERNAL_REFERENCE_KINDS = new Set([
  'api-observation',
  'human-input',
  'human-provided-artifact',
  'runtime-observation',
  'web-direct-capture',
  'web-page',
]);

export function projectFactReadingAssociations(obj: Record<string, unknown>): FactReadingAssociations {
  const unresolved: UnresolvedAssociation[] = [];
  const sourceMaterials = projectReferenceArray(obj.source_refs, 'source', 'source_refs', unresolved);
  const evidenceMaterials = projectReferenceArray(obj.evidence_refs, 'evidence', 'evidence_refs', unresolved);
  const relations = projectRelations(obj.relations, unresolved);

  return {
    relations,
    projectMaterials: sourceMaterials.filter((item) => item.category === 'project'),
    externalInputs: sourceMaterials.filter((item) => item.category === 'external'),
    evidenceMaterials,
    unresolved: [
      ...unresolved,
      ...sourceMaterials
        .filter((item) => item.category === 'unresolved')
        .map((item) => ({ originPath: item.originPath, role: item.role, value: item })),
    ],
  };
}

function projectRelations(value: unknown, unresolved: UnresolvedAssociation[]): ReadingRelation[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) {
    unresolved.push({ originPath: 'relations', role: 'relation', value });
    return [];
  }

  return value.flatMap((item, index) => {
    const originPath = `relations[${index}]`;
    if (!isRecord(item) || typeof item.relation_key !== 'string' || !isRecord(item.target)) {
      unresolved.push({ originPath, role: 'relation', value: item });
      return [];
    }
    const target = item.target;
    if (
      typeof target.governed_project_id !== 'string'
      || typeof target.fact_type_key !== 'string'
      || typeof target.object_id !== 'string'
    ) {
      unresolved.push({ originPath, role: 'relation', value: item });
      return [];
    }

    return [{
      originPath,
      relationKey: item.relation_key,
      target: {
        governedProjectId: target.governed_project_id,
        factTypeKey: target.fact_type_key,
        objectId: target.object_id,
        governanceRefs: projectReferenceArray(
          target.governance_refs,
          'governance',
          `${originPath}.target.governance_refs`,
          unresolved,
        ),
      },
      sourceRefs: projectReferenceArray(item.source_refs, 'relation-source', `${originPath}.source_refs`, unresolved),
    }];
  });
}

function projectReferenceArray(
  value: unknown,
  role: ReferenceRole,
  fieldPath: string,
  unresolved: UnresolvedAssociation[],
): ReadingMaterial[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) {
    unresolved.push({ originPath: fieldPath, role, value });
    return [];
  }

  return value.flatMap((item, index) => {
    const originPath = `${fieldPath}[${index}]`;
    if (!isRecord(item) || typeof item.kind !== 'string' || typeof item.locator !== 'string') {
      unresolved.push({ originPath, role, value: item });
      return [];
    }
    return [{
      originPath,
      role,
      category: getMaterialCategory(item.kind, item.locator),
      kind: item.kind,
      locator: item.locator,
      version: nonEmptyString(item.version),
      observedAt: nonEmptyString(item.observed_at),
    }];
  });
}

function getMaterialCategory(kind: string, locator: string): MaterialCategory {
  if (PROJECT_REFERENCE_KINDS.has(kind)) return 'project';
  if (EXTERNAL_REFERENCE_KINDS.has(kind) || /^https?:\/\//i.test(locator) || locator.startsWith('data:')) {
    return 'external';
  }
  return 'unresolved';
}

function nonEmptyString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim().length > 0 ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
