export type ReadingRelation = {
  originPath: string;
  relationKey: string;
  target: {
    governedProjectId: string;
    factTypeKey: string;
    objectId: string;
  };
};

export type UnresolvedAssociation = {
  originPath: string;
  role: 'relation';
  value: unknown;
};

export type FactReadingAssociations = {
  relations: ReadingRelation[];
  unresolved: UnresolvedAssociation[];
};

export type RelationTargetTypeGroup = {
  factTypeKey: string;
  relations: ReadingRelation[];
};

/** Project only the two-part fact-object relation contract. */
export function projectFactReadingAssociations(obj: Record<string, unknown>): FactReadingAssociations {
  const unresolved: UnresolvedAssociation[] = [];
  return { relations: dedupeRelationsByTarget(projectRelations(obj.relations, unresolved)), unresolved };
}

/** Multiple formal relation keys can describe one target, but reading presents it once. */
function dedupeRelationsByTarget(relations: ReadingRelation[]): ReadingRelation[] {
  const seenTargets = new Set<string>();
  return relations.filter((relation) => {
    const { governedProjectId, factTypeKey, objectId } = relation.target;
    const targetKey = `${governedProjectId}\u0000${factTypeKey}\u0000${objectId}`;
    if (seenTargets.has(targetKey)) return false;
    seenTargets.add(targetKey);
    return true;
  });
}

/**
 * A plain relation only says that two fact objects are associated.  The reading
 * view therefore groups by the target's object type, not by relation_key.
 */
export function groupRelationsByTargetType(relations: ReadingRelation[]): RelationTargetTypeGroup[] {
  const grouped = new Map<string, ReadingRelation[]>();
  for (const relation of relations) {
    grouped.set(relation.target.factTypeKey, [...(grouped.get(relation.target.factTypeKey) ?? []), relation]);
  }
  return [...grouped.entries()].map(([factTypeKey, items]) => ({ factTypeKey, relations: items }));
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
      },
    }];
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
