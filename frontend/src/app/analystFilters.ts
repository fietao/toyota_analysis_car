export type AnalystFilterRow = {
  brand: string;
  model?: string;
  is_grand_total?: boolean;
};

export function selectAnalystFilterOptions(rows: AnalystFilterRow[], selectedBrand: string) {
  const brands = new Set<string>();
  const models = new Set<string>();

  rows.forEach((row) => {
    if (row.is_grand_total) return;
    if (row.brand) brands.add(row.brand);
    if ((!selectedBrand || row.brand === selectedBrand) && row.model) models.add(row.model);
  });

  return {
    brands: Array.from(brands).sort(),
    models: Array.from(models).sort(),
  };
}

export function filterAnalystRows<T extends AnalystFilterRow>(
  rows: T[],
  selectedBrand: string,
  selectedModel: string,
) {
  return rows.filter((row) => {
    if (row.is_grand_total) return true;
    if (selectedBrand && row.brand !== selectedBrand) return false;
    return !selectedModel || row.model === selectedModel;
  });
}
