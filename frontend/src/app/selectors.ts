export const VEHICLE_TYPE_DICT: Record<string, string> = {
  "รย.1": "รย.1 (รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน / เก๋ง)",
  "รย.2": "รย.2 (รถยนต์นั่งส่วนบุคคลเกิน 7 คน / ตู้)",
  "รย.3": "รย.3 (รถยนต์บรรทุกส่วนบุคคล / กระบะ)",
  "รย.6": "รย.6 (รถยนต์รับจ้างบรรทุกคนโดยสารไม่เกิน 7 คน / แท็กซี่)",
  "รย.9": "รย.9 (รถยนต์บริการธุรกิจ)",
  "รย.10": "รย.10 (รถยนต์บริการทัศนาจร)",
  "รย.11": "รย.11 (รถยนต์บริการให้เช่า / รถเช่า)"
};

export type PowertrainMasterRow = { f: string; pt: string; y: number; u: number };
export type FuelRow = { y: number; m: string; pt: string; f: string; v: string; u: number };
export type TreeMonthly = Record<string, Record<string, Record<string, number[]>>>;

export type ModelNode = {
  name: string;
  fuel: string;
  monthly: TreeMonthly;
};

export type BrandNode = {
  brand: string;
  powertrain: string;
  fuel: string;
  monthly: TreeMonthly;
  models: ModelNode[];
};

export type DashboardData = {
  meta: { 
    years: number[]; 
    months: string[]; 
    provinces: string[]; 
    vehicle_types_list?: { code: string; label: string }[];
  };
  powertrain_master: PowertrainMasterRow[];
  fuel_monthly: FuelRow[];
  brand_model_tree: BrandNode[];
};

export type Rec = Record<string, string | number | boolean | null>;

export function getNodeSums(node: { monthly: TreeMonthly }, selectedYear: number | "All", selectedVehicleTypes: string[], selectedProvinces: string[]) {
  const timeVals: Record<string, number> = {};
  let grandTotal = 0;
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  const vcs = selectedVehicleTypes.length > 0 ? selectedVehicleTypes : Object.keys(node.monthly || {});

  vcs.forEach(vc => {
    const vcBucket = node.monthly?.[vc];
    if (!vcBucket) return;
    
    const provs = selectedProvinces.length > 0 ? selectedProvinces : Object.keys(vcBucket);
    provs.forEach(prov => {
      const pBucket = vcBucket[prov];
      if (!pBucket) return;

      Object.keys(pBucket).forEach(yStr => {
        if (selectedYear !== "All" && yStr !== String(selectedYear)) return;

        const arr = pBucket[yStr];
        if (!Array.isArray(arr)) return;

        if (selectedYear === "All") {
          let ySum = 0;
          for (let i = 0; i < 12; i++) ySum += arr[i] || 0;
          timeVals[yStr] = (timeVals[yStr] || 0) + ySum;
          grandTotal += ySum;
        } else {
          for (let i = 0; i < 12; i++) {
            const mStr = months[i];
            timeVals[mStr] = (timeVals[mStr] || 0) + (arr[i] || 0);
            grandTotal += (arr[i] || 0);
          }
        }
      });
    });
  });

  return { timeVals, grandTotal };
}

export function determineProvinceStatus(
  share: number,
  totalProvVol: number,
  p25: number,
  p50: number
): string {
  if (share >= 0.15) return "Stronghold";
  if (share >= 0.05) return "Growth Market";
  if (totalProvVol < p25) return "Low Demand";
  if (share === 0 && totalProvVol >= p50) return "Possible Gap";
  if (share < 0.03 && totalProvVol >= p50) return "Weak Spot";
  return "Average";
}

export function selectFilterOptions(data: DashboardData | null, rankingBrand: string[]) {
  if (!data?.brand_model_tree) return { allDataBrands: [], allDataModels: [] };
  
  const allDataBrands = Array.from(new Set(data.brand_model_tree.map(b => b.brand))).sort();
  
  const mSet = new Set<string>();
  data.brand_model_tree.forEach(b => {
    const cleanBrand = b.brand;
    if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;
    
    b.models?.forEach(m => mSet.add(m.name));
  });
  const allDataModels = Array.from(mSet).sort();
  
  return { allDataBrands, allDataModels };
}

export function selectTrendData(
  data: DashboardData | null,
  selectedYear: number | "All",
  selectedVehicleTypes: string[],
  trendGroupBy: "Powertrain" | "Vehicle Type",
  timeKeys: string[]
) {
  if (!data?.fuel_monthly) return { trendKeys: [], trendData: [], trendTable: [] };

  const d = selectedVehicleTypes.length > 0 
    ? data.fuel_monthly.filter(x => selectedVehicleTypes.includes(x.v))
    : data.fuel_monthly;
  const fuelFiltered = selectedYear === "All" ? d : d.filter(x => x.y === selectedYear);

  let trendKeys: string[] = [];
  if (trendGroupBy === "Powertrain") {
    trendKeys = ["ICE", "BEV", "HEV", "PHEV"];
  } else {
    trendKeys = Array.from(new Set(fuelFiltered.map(x => VEHICLE_TYPE_DICT[x.v] || x.v)));
  }

  const res: Rec[] = [];
  timeKeys.forEach(t => {
    const point: Rec = { name: t, Total: 0 };
    
    if (trendGroupBy === "Powertrain") {
      ["ICE", "BEV", "HEV", "PHEV"].forEach(pt => {
        const sum = fuelFiltered
          .filter(x => x.pt === pt && String(selectedYear === "All" ? x.y : x.m) === t)
          .reduce((acc, curr) => acc + curr.u, 0);
        point[pt] = sum;
        point.Total = Number(point.Total) + sum;
      });
    } else {
      trendKeys.forEach(vKey => {
        const sum = fuelFiltered
          .filter(x => (VEHICLE_TYPE_DICT[x.v] || x.v) === vKey && String(selectedYear === "All" ? x.y : x.m) === t)
          .reduce((acc, curr) => acc + curr.u, 0);
        point[vKey] = sum;
        point.Total = Number(point.Total) + sum;
      });
    }

    res.push(point);
  });
  
  let lastValidIdx = res.length - 1;
  while (lastValidIdx >= 0 && res[lastValidIdx].Total === 0) lastValidIdx--;
  const trendData = res.slice(0, lastValidIdx + 1);

  const trendTable: Rec[] = [];
  [...trendKeys, "Total"].forEach(key => {
    const row: Rec = { name: key === "Total" ? "Grand Total" : key, YTD: 0 };
    timeKeys.forEach(t => {
      const val = trendData.find(x => x.name === t)?.[key] ?? 0;
      row[t] = val;
      row.YTD = Number(row.YTD) + Number(val);
    });
    trendTable.push(row);
  });

  return { trendKeys, trendData, trendTable: trendTable.filter(r => Number(r.YTD) > 0) };
}

export function selectRankingsData(
  data: DashboardData | null,
  rankingPt: string[],
  rankingBrand: string[],
  rankingModel: string[],
  rankingProvince: string[],
  expandedBrands: Set<string>,
  selectedYear: number | "All",
  selectedVehicleTypes: string[],
  timeKeys: string[]
) {
  if (!data?.brand_model_tree) return { rows: [], totalUnits: 0, bevUnits: 0, ptMix: [] };

  const map = new Map<string, Rec>();
  const modelsMap = new Map<string, Rec[]>(); // parentId -> array of model rows

  let totalUnits = 0;
  let bevUnits = 0;
  const ptMixMap: Record<string, number> = { ICE: 0, BEV: 0, HEV: 0, PHEV: 0 };

  data.brand_model_tree.forEach(brandNode => {
    if (rankingPt.length > 0 && !rankingPt.includes(brandNode.powertrain)) return;
    const cleanBrand = brandNode.brand;
    if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;

    const key = cleanBrand;
    if (!map.has(key)) {
       const row: Rec = { 
          id: key, name: cleanBrand, YTD: 0, 
          hasChildren: (brandNode.models?.length ?? 0) > 0, 
          isExpanded: expandedBrands.has(key) 
       };
       timeKeys.forEach(t => row[t] = 0);
       map.set(key, row);
       modelsMap.set(key, []);
    }
    const row = map.get(key)!;
    // Update hasChildren in case we see models later
    if ((brandNode.models?.length ?? 0) > 0) row.hasChildren = true;
    row.isExpanded = expandedBrands.has(key);

    const { timeVals, grandTotal } = getNodeSums(brandNode, selectedYear, selectedVehicleTypes, rankingProvince);
    
    timeKeys.forEach(t => { row[t] = Number(row[t]) + (timeVals[t] || 0); });
    row.YTD = Number(row.YTD) + grandTotal;

    totalUnits += grandTotal;
    if (brandNode.powertrain === "BEV") bevUnits += grandTotal;
    if (brandNode.powertrain in ptMixMap) ptMixMap[brandNode.powertrain] += grandTotal;

    // Calculate models if expanded
    if (expandedBrands.has(key)) {
       brandNode.models?.forEach(model => {
          if (rankingModel.length > 0 && !rankingModel.includes(model.name)) return;
          const mKey = `${key}|${model.name}`;
          const mList = modelsMap.get(key)!;
          let mRow = mList.find(r => r.id === mKey);
          if (!mRow) {
             mRow = { id: mKey, parentId: key, name: model.name, YTD: 0, isSubRow: true };
             timeKeys.forEach(t => mRow![t] = 0);
             mList.push(mRow);
          }
          const mSums = getNodeSums(model, selectedYear, selectedVehicleTypes, rankingProvince);
          timeKeys.forEach(t => { mRow![t] = Number(mRow![t]) + (mSums.timeVals[t] || 0); });
          mRow!.YTD = Number(mRow!.YTD) + mSums.grandTotal;
       });
    }
  });

  // Assemble final flat array correctly preserving hierarchy for the table
  const finalRows: Rec[] = [];
  const sortedBrands = Array.from(map.values())
     .filter(r => Number(r.YTD) > 0)
     .sort((a, b) => Number(b.YTD) - Number(a.YTD))
     .map((r, i) => ({ ...r, rank: i + 1 } as Rec));

  sortedBrands.forEach(b => {
     finalRows.push(b);
     if (expandedBrands.has(String(b.id))) {
        const mList = modelsMap.get(String(b.id)) || [];
        const sortedModels = mList
           .filter(r => Number(r.YTD) > 0)
           .sort((a, b) => Number(b.YTD) - Number(a.YTD));
        finalRows.push(...sortedModels);
     }
  });

  const ptMix = Object.entries(ptMixMap).map(([name, val]) => ({ name, YTD: val })).filter(d => d.YTD > 0);

  return { rows: finalRows, totalUnits, bevUnits, ptMix };
}

export function selectDynamicChartData(
  data: DashboardData | null,
  chartGroupBy: "Brands" | "Models" | "Provinces",
  rankingPt: string[],
  rankingBrand: string[],
  rankingModel: string[],
  rankingProvince: string[],
  selectedYear: number | "All",
  selectedVehicleTypes: string[]
) {
  if (!data?.brand_model_tree) return [];
  const cMap = new Map<string, number>();

  data.brand_model_tree.forEach(brandNode => {
    if (rankingPt.length > 0 && !rankingPt.includes(brandNode.powertrain)) return;
    const cleanBrand = brandNode.brand;
    if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;

    if (chartGroupBy === "Brands") {
       const { grandTotal } = getNodeSums(brandNode, selectedYear, selectedVehicleTypes, rankingProvince);
       cMap.set(cleanBrand, (cMap.get(cleanBrand) || 0) + grandTotal);
    } else if (chartGroupBy === "Models") {
       brandNode.models?.forEach(model => {
          if (rankingModel.length > 0 && !rankingModel.includes(model.name)) return;
          const { grandTotal } = getNodeSums(model, selectedYear, selectedVehicleTypes, rankingProvince);
          const label = `${cleanBrand} ${model.name}`;
          cMap.set(label, (cMap.get(label) || 0) + grandTotal);
       });
    } else if (chartGroupBy === "Provinces") {
       const vcs = selectedVehicleTypes.length > 0 ? selectedVehicleTypes : Object.keys(brandNode.monthly || {});
       vcs.forEach(vc => {
          const vcBucket = brandNode.monthly?.[vc];
          if (!vcBucket) return;
          Object.keys(vcBucket).forEach(prov => {
             if (rankingProvince.length > 0 && !rankingProvince.includes(prov)) return;
             const pBucket = vcBucket[prov];
             let pTotal = 0;
             Object.keys(pBucket).forEach(yStr => {
                if (selectedYear !== "All" && yStr !== String(selectedYear)) return;
                const arr = pBucket[yStr];
                if (Array.isArray(arr)) for (let i=0; i<12; i++) pTotal += arr[i] || 0;
             });
             cMap.set(prov, (cMap.get(prov) || 0) + pTotal);
          });
       });
    }
  });

  return Array.from(cMap.entries())
    .map(([name, YTD]) => ({ name, YTD }))
    .sort((a, b) => b.YTD - a.YTD)
    .slice(0, 10);
}

export function selectProvinceAnalysisData(
  data: DashboardData | null,
  trendProvBrand: string,
  trendProvModel: string,
  selectedVehicleTypes: string[],
  selectedYear: number | "All"
) {
  if (!data?.brand_model_tree) return [];
  const provMap = new Map<string, { prov: string; totalProvVol: number; selectedVol: number; rankMap: Map<string, number> }>();
  
  const targetKey = trendProvBrand && trendProvModel ? `${trendProvBrand}|${trendProvModel}` : trendProvBrand;

  data.brand_model_tree.forEach(brandNode => {
    const cleanBrand = brandNode.brand;

    const processNode = (node: { monthly: TreeMonthly }, isSelected: boolean, key: string) => {
      const vcs = selectedVehicleTypes.length > 0 ? selectedVehicleTypes : Object.keys(node.monthly || {});
      vcs.forEach(vc => {
        const vcBucket = node.monthly?.[vc];
        if (!vcBucket) return;
        Object.keys(vcBucket).forEach(prov => {
          const pBucket = vcBucket[prov];
          if (!pBucket) return;
          let sum = 0;
          Object.keys(pBucket).forEach(yStr => {
            if (selectedYear !== "All" && yStr !== String(selectedYear)) return;
            const arr = pBucket[yStr];
            if (Array.isArray(arr)) {
              for (let i = 0; i < 12; i++) sum += arr[i] || 0;
            }
          });
          if (sum > 0) {
             if (!provMap.has(prov)) provMap.set(prov, { prov, totalProvVol: 0, selectedVol: 0, rankMap: new Map() });
             const pData = provMap.get(prov)!;
             pData.totalProvVol += sum;
             if (isSelected) pData.selectedVol += sum;
             pData.rankMap.set(key, (pData.rankMap.get(key) || 0) + sum);
          }
        });
      });
    };

    if (trendProvBrand && trendProvModel) {
       brandNode.models?.forEach(model => {
          const key = `${cleanBrand}|${model.name}`;
          const isModelSelected = key === targetKey;
          processNode(model, isModelSelected, key);
       });
    } else {
       const isBrandSelected = cleanBrand === targetKey;
       processNode(brandNode, isBrandSelected, cleanBrand);
    }
  });

  const res = Array.from(provMap.values()).map(p => {
    const share = p.totalProvVol > 0 ? p.selectedVol / p.totalProvVol : 0;
    let topCompetitor = "None";
    let topCompVol = 0;
    let myRank: number | string = "—";
    
    const ranks = Array.from(p.rankMap.entries()).sort((a, b) => b[1] - a[1]);
    
    if (!targetKey) {
       myRank = "—";
    } else {
       let rankCounter = 1;
       let foundMe = false;
       for (const [key, vol] of ranks) {
          if (key === targetKey) {
              myRank = rankCounter;
              foundMe = true;
          } else {
              if (vol > topCompVol) {
                 topCompetitor = key.includes("|") ? key.split("|")[1] : key;
                 topCompVol = vol;
              }
          }
          rankCounter++;
       }
       if (!foundMe) myRank = "—";
    }

    return { ...p, share, topCompetitor, myRank };
  });

  const sortedByVol = [...res].sort((a,b) => b.totalProvVol - a.totalProvVol);
  const p25 = sortedByVol[Math.floor(sortedByVol.length * 0.75)]?.totalProvVol || 0;
  const p50 = sortedByVol[Math.floor(sortedByVol.length * 0.5)]?.totalProvVol || 0;

  return res.map(p => {
    const status = determineProvinceStatus(p.share, p.totalProvVol, p25, p50);

    let shareStr = "—";
    if (p.totalProvVol > 0) {
       if (p.selectedVol > 0 && p.share < 0.0005) shareStr = "<0.1%";
       else shareStr = (p.share * 100).toFixed(1) + "%";
    }

    const { rankMap, ...rest } = p;
    return {
      ...rest,
      status,
      shareStr
    };
  });
}
