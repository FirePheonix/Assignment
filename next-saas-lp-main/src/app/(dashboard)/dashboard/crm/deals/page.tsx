"use client";

import { DollarSign, Search, Plus, TrendingUp, Calendar, Building2 } from "lucide-react";

export default function CRMDealsPage() {
  const stages = [
    { name: "Prospecting", count: 8, value: 125000 },
    { name: "Qualification", count: 5, value: 87500 },
    { name: "Proposal", count: 3, value: 156000 },
    { name: "Negotiation", count: 2, value: 98000 },
    { name: "Closed Won", count: 12, value: 450000 },
  ];

  const deals = [
    {
      id: 1,
      name: "Enterprise Plan - Acme Corp",
      company: "Acme Corporation",
      value: 50000,
      stage: "Proposal",
      probability: 65,
      closeDate: "2025-12-30",
      contact: "John Smith",
      daysInStage: 5,
    },
    {
      id: 2,
      name: "Annual Subscription - Tech Solutions",
      company: "Tech Solutions Inc",
      value: 35000,
      stage: "Negotiation",
      probability: 80,
      closeDate: "2025-12-25",
      contact: "Sarah Johnson",
      daysInStage: 3,
    },
    {
      id: 3,
      name: "Marketing Package - Digital Ventures",
      company: "Digital Ventures LLC",
      value: 15000,
      stage: "Qualification",
      probability: 45,
      closeDate: "2026-01-15",
      contact: "Michael Chen",
      daysInStage: 12,
    },
    {
      id: 4,
      name: "Premium Plan - Growth Partners",
      company: "Growth Partners",
      value: 75000,
      stage: "Proposal",
      probability: 70,
      closeDate: "2025-12-28",
      contact: "Emily Rodriguez",
      daysInStage: 7,
    },
  ];

  const getStageColor = (stage: string) => {
    switch (stage) {
      case "Prospecting":
        return "bg-gray-500/20 text-gray-400";
      case "Qualification":
        return "bg-blue-500/20 text-blue-400";
      case "Proposal":
        return "bg-purple-500/20 text-purple-400";
      case "Negotiation":
        return "bg-orange-500/20 text-orange-400";
      case "Closed Won":
        return "bg-green-500/20 text-green-400";
      default:
        return "bg-gray-500/20 text-gray-400";
    }
  };

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Deals Pipeline</h1>
        <p className="text-gray-400">Track and manage your sales opportunities</p>
      </div>

      {/* Actions Bar */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search deals..."
            className="w-full pl-10 pr-4 py-3 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
          <option>All Stages</option>
          <option>Prospecting</option>
          <option>Qualification</option>
          <option>Proposal</option>
          <option>Negotiation</option>
        </select>
        <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Deal
        </button>
      </div>

      {/* Pipeline Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        {stages.map((stage, i) => (
          <div key={i} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">{stage.name}</h3>
            <p className="text-2xl font-bold text-white">${(stage.value / 1000).toFixed(0)}K</p>
            <p className="text-sm text-gray-400 mt-1">{stage.count} deals</p>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Total Pipeline Value</p>
          <p className="text-2xl font-bold text-white mt-1">$916K</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Weighted Value</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">$548K</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Avg Deal Size</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">$30.5K</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Win Rate</p>
          <p className="text-2xl font-bold text-green-400 mt-1">68%</p>
        </div>
      </div>

      {/* Deals List */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
          <div className="col-span-3">Deal Name</div>
          <div className="col-span-2">Company</div>
          <div className="col-span-1">Value</div>
          <div className="col-span-2">Stage</div>
          <div className="col-span-2">Close Date</div>
          <div className="col-span-1">Probability</div>
          <div className="col-span-1">Actions</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/10">
          {deals.map((deal) => (
            <div
              key={deal.id}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
            >
              {/* Deal Name */}
              <div className="col-span-3 flex flex-col justify-center">
                <p className="text-white font-medium">{deal.name}</p>
                <p className="text-sm text-gray-400">{deal.contact}</p>
              </div>

              {/* Company */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400">
                  <Building2 className="w-4 h-4" />
                  <span className="text-sm">{deal.company}</span>
                </div>
              </div>

              {/* Value */}
              <div className="col-span-1 flex items-center">
                <div className="flex items-center gap-1 text-white">
                  <DollarSign className="w-4 h-4" />
                  <span className="font-medium">{(deal.value / 1000).toFixed(0)}K</span>
                </div>
              </div>

              {/* Stage */}
              <div className="col-span-2 flex items-center">
                <span className={`text-xs px-3 py-1 rounded ${getStageColor(deal.stage)}`}>
                  {deal.stage}
                </span>
              </div>

              {/* Close Date */}
              <div className="col-span-2 flex flex-col justify-center">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Calendar className="w-3 h-3" />
                  <span>{deal.closeDate}</span>
                </div>
                <p className="text-xs text-gray-500">{deal.daysInStage} days in stage</p>
              </div>

              {/* Probability */}
              <div className="col-span-1 flex items-center">
                <div className="w-full">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400">{deal.probability}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                      style={{ width: `${deal.probability}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="col-span-1 flex items-center justify-end gap-2">
                <button className="text-blue-400 hover:text-blue-300 text-sm px-3 py-1 rounded hover:bg-blue-500/10 transition">
                  View
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 bg-black border-t border-white/10 flex items-center justify-between">
          <p className="text-sm text-gray-400">Showing 1-4 of 30 deals</p>
          <div className="flex items-center gap-2">
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">
              Previous
            </button>
            <button className="bg-purple-600 text-white px-3 py-1 rounded">1</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">2</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
