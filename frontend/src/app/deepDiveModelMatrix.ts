import {
  type BrandNode,
  type ModelNode,
  type TreeMonthly,
  brandTotals,
  seriesTotals,
} from "./selectors.ts";

export type DeepDiveFilters = {
  activeYears: string[];
  selectedBrands: string[];
  selectedModels: string[];
  selectedProvinces: string[];
  selectedVehicleTypes: string[];
};

export type SeriesRow = ModelNode & { totals: { grandTotal: number; ytdTotal: number } };
export type BrandRow = Omit<BrandNode, "models"> & {
  toggleKey: string;
  isExpanded: boolean;
  totals: { grandTotal: number; ytdTotal: number };
  models: SeriesRow[];
};

function collectMonthlyProvinces(monthly: TreeMonthly | undefined, provinces: Set<string>) {
  Object.values(monthly || {}).forEach((vehicleBucket) => {
    Object.keys(vehicleBucket || {}).forEach((province) => {
      if (province) provinces.add(province);
    });
  });
}

export function selectDeepDiveMatrixOptions(
  tree: BrandNode[] | undefined,
  selectedBrands: string[],
  metaProvinces: string[] = []
) {
  const brandsSet = new Set<string>();
  const modelsSet = new Set<string>();
  const provincesSet = new Set(metaProvinces);

  tree?.forEach((node) => {
    if (node.brand) brandsSet.add(node.brand);
    collectMonthlyProvinces(node.monthly, provincesSet);

    if (selectedBrands.length > 0 && !selectedBrands.includes(node.brand)) return;
    node.models?.forEach((model) => {
      if (model.name) modelsSet.add(model.name);
      collectMonthlyProvinces(model.monthly, provincesSet);
      model.segments?.forEach((segment) => collectMonthlyProvinces(segment.monthly, provincesSet));
    });
  });

  return {
    allBrands: Array.from(brandsSet).sort(),
    allModels: Array.from(modelsSet).sort(),
    allProvinces: Array.from(provincesSet).sort(),
  };
}

export function deepDiveFilterKey(filters: DeepDiveFilters) {
  return [
    filters.selectedBrands.join(","),
    filters.selectedModels.join(","),
    filters.selectedProvinces.join(","),
    filters.selectedVehicleTypes.join(","),
    filters.activeYears.join(","),
  ].join("|");
}

export function buildDeepDiveMatrixRows(
  tree: BrandNode[] | undefined,
  filters: DeepDiveFilters,
  latestYear: string | null,
  expandedBrands: Set<string>
): BrandRow[] {
  if (!tree) return [];

  return tree
    .map((brandNode): BrandRow | null => {
      if (filters.selectedBrands.length > 0 && !filters.selectedBrands.includes(brandNode.brand)) return null;

      const toggleKey = brandNode.brand;
      const isExpanded = expandedBrands.has(toggleKey);

      const bTotals = brandTotals(
        brandNode,
        filters.activeYears,
        latestYear,
        [],
        filters.selectedVehicleTypes,
        filters.selectedProvinces
      );
      if (bTotals.grandTotal === 0) return null;

      const filteredModels = (brandNode.models || [])
        .map((model): SeriesRow | null => {
          if (filters.selectedModels.length > 0 && !filters.selectedModels.includes(model.name)) return null;
          const mTotals = seriesTotals(
            model,
            filters.activeYears,
            latestYear,
            [],
            filters.selectedVehicleTypes,
            filters.selectedProvinces
          );
          if (mTotals.grandTotal === 0) return null;
          return { ...model, totals: mTotals };
        })
        .filter((m): m is SeriesRow => m !== null)
        .sort((a, b) => b.totals.grandTotal - a.totals.grandTotal);

      return {
        ...brandNode,
        toggleKey,
        isExpanded,
        totals: bTotals,
        models: filteredModels,
      };
    })
    .filter((b): b is BrandRow => b !== null)
    .sort((a, b) => b.totals.grandTotal - a.totals.grandTotal);
}

export function referenceDeepDiveTotal(tree: BrandNode[] | undefined) {
  let sum = 0;
  tree?.forEach((brandNode) => {
    Object.values(brandNode.monthly || {}).forEach((vehicleBucket) => {
      Object.values(vehicleBucket || {}).forEach((provinceBucket) => {
        Object.values(provinceBucket || {}).forEach((arr) => {
          sum += (arr || []).reduce((s, v) => s + (v || 0), 0);
        });
      });
    });
  });
  return sum;
}
