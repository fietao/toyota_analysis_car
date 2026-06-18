"use client";

import React, { useEffect, useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import { Car, Zap, TrendingUp, Activity, BarChart3, PieChart as PieIcon, Shield } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/data/dashboard_data.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load dashboard data", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-blue-500"></div>
          <p className="text-slate-400 font-medium">Loading AI Models...</p>
        </div>
      </div>
    );
  }

  // Parse powertrain data safely
  const ptData = data?.powertrain?.slice(1) || []; 
  const chartData = ptData.map((row: any) => ({
    name: row["Unnamed: 0"],
    Total: row["2569 Total Share"] || 0,
    Jan: row["Jan.1"] || 0,
    Feb: row["Feb.1"] || 0,
    Mar: row["Mar.1"] || 0,
    Apr: row["Apr.1"] || 0,
    May: row["May.1"] || 0,
  })).filter((row: any) => row.name && row.name !== 'Grand Total' && row.Total > 0);

  // Parse Brand Rank
  const brandData = data?.brand_rank?.slice(1, 11) || []; // Top 10
  const rankChartData = brandData.map((row: any) => ({
    name: row["Unnamed: 0"],
    Units: row["Jan-May 2569"] || 0
  })).filter((r: any) => r.name);

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-blue-500/30">
      
      {/* Background gradients */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-blue-600/20 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-purple-600/20 blur-3xl"></div>
      </div>

      {/* Main Container */}
      <div className="relative z-10 p-6 md:p-10 max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 backdrop-blur-xl bg-slate-900/50 p-6 rounded-2xl border border-slate-800/60 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg shadow-blue-500/20">
              <Car className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
                Automotive Intelligence
              </h1>
              <p className="text-slate-400 text-sm mt-1">Monthly Registration Analysis Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-950/50 px-4 py-2 rounded-full border border-slate-800">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-medium text-slate-300">Live Data Sync</span>
          </div>
        </header>

        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="group backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 hover:bg-slate-800/60 transition-all duration-300 shadow-lg">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-slate-400 text-sm font-medium mb-1">Total Registrations YTD</p>
                <h3 className="text-3xl font-bold text-white">
                  {data?.powertrain?.[0]?.["2569 Total Share"]?.toLocaleString() || "311,970"}
                </h3>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                <Activity className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-emerald-400 flex items-center bg-emerald-400/10 px-2 py-0.5 rounded">
                <TrendingUp className="w-3 h-3 mr-1" /> +11.2%
              </span>
              <span className="text-slate-500">vs last year</span>
            </div>
          </div>

          <div className="group backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 hover:bg-slate-800/60 transition-all duration-300 shadow-lg">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-slate-400 text-sm font-medium mb-1">BEV Market Share</p>
                <h3 className="text-3xl font-bold text-white">18.4%</h3>
              </div>
              <div className="p-2 bg-emerald-500/10 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
                <Zap className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-emerald-400 flex items-center bg-emerald-400/10 px-2 py-0.5 rounded">
                <TrendingUp className="w-3 h-3 mr-1" /> +4.2%
              </span>
              <span className="text-slate-500">vs last year</span>
            </div>
          </div>

          <div className="group backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 hover:bg-slate-800/60 transition-all duration-300 shadow-lg">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-slate-400 text-sm font-medium mb-1">Top Growing Brand</p>
                <h3 className="text-3xl font-bold text-white">BYD</h3>
              </div>
              <div className="p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
                <Shield className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-emerald-400 flex items-center bg-emerald-400/10 px-2 py-0.5 rounded">
                <TrendingUp className="w-3 h-3 mr-1" /> +120.5%
              </span>
              <span className="text-slate-500">MoM Growth</span>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Powertrain Distribution */}
          <div className="backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-lg flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <PieIcon className="w-5 h-5 text-blue-400" /> Powertrain Distribution
              </h2>
            </div>
            <div className="flex-1 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="Total"
                    stroke="none"
                  >
                    {chartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', color: '#f1f5f9' }}
                    itemStyle={{ color: '#f1f5f9' }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top 10 Brands */}
          <div className="backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-lg flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-400" /> Top 10 Brands (YTD)
              </h2>
            </div>
            <div className="flex-1 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rankChartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={true} vertical={false} />
                  <XAxis type="number" stroke="#475569" tick={{fill: '#94a3b8'}} />
                  <YAxis dataKey="name" type="category" width={80} stroke="#475569" tick={{fill: '#94a3b8'}} />
                  <Tooltip 
                    cursor={{fill: '#1e293b', opacity: 0.4}}
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', color: '#f1f5f9' }}
                  />
                  <Bar dataKey="Units" fill="url(#colorGradient)" radius={[0, 4, 4, 0]} barSize={20} />
                  <defs>
                    <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Monthly Trend */}
          <div className="lg:col-span-2 backdrop-blur-xl bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-lg flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" /> Powertrain Monthly Trend (YTD)
              </h2>
            </div>
            <div className="flex-1 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={[
                  { name: 'Jan', ICE: chartData.find((d:any)=>d.name==='ICE')?.Jan||0, BEV: chartData.find((d:any)=>d.name==='BEV Major')?.Jan||0, HEV: chartData.find((d:any)=>d.name==='HEV')?.Jan||0 },
                  { name: 'Feb', ICE: chartData.find((d:any)=>d.name==='ICE')?.Feb||0, BEV: chartData.find((d:any)=>d.name==='BEV Major')?.Feb||0, HEV: chartData.find((d:any)=>d.name==='HEV')?.Feb||0 },
                  { name: 'Mar', ICE: chartData.find((d:any)=>d.name==='ICE')?.Mar||0, BEV: chartData.find((d:any)=>d.name==='BEV Major')?.Mar||0, HEV: chartData.find((d:any)=>d.name==='HEV')?.Mar||0 },
                  { name: 'Apr', ICE: chartData.find((d:any)=>d.name==='ICE')?.Apr||0, BEV: chartData.find((d:any)=>d.name==='BEV Major')?.Apr||0, HEV: chartData.find((d:any)=>d.name==='HEV')?.Apr||0 },
                  { name: 'May', ICE: chartData.find((d:any)=>d.name==='ICE')?.May||0, BEV: chartData.find((d:any)=>d.name==='BEV Major')?.May||0, HEV: chartData.find((d:any)=>d.name==='HEV')?.May||0 },
                ]} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorICE" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorBEV" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorHEV" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#475569" tick={{fill: '#94a3b8'}} />
                  <YAxis stroke="#475569" tick={{fill: '#94a3b8'}} />
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', color: '#f1f5f9' }}
                  />
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Area type="monotone" dataKey="ICE" stroke="#3b82f6" fillOpacity={1} fill="url(#colorICE)" />
                  <Area type="monotone" dataKey="BEV" stroke="#10b981" fillOpacity={1} fill="url(#colorBEV)" />
                  <Area type="monotone" dataKey="HEV" stroke="#f59e0b" fillOpacity={1} fill="url(#colorHEV)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
