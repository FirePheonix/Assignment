"use client";

import { FileText, Eye, TrendingUp, Clock, ExternalLink } from "lucide-react";

export default function AnalyticsPagesPage() {
  const pages = [
    {
      path: "/",
      title: "Home",
      views: 12340,
      uniqueVisitors: 4521,
      avgTime: "3m 45s",
      bounceRate: 38.2,
      conversions: 156,
    },
    {
      path: "/pricing",
      title: "Pricing",
      views: 8760,
      uniqueVisitors: 3210,
      avgTime: "4m 12s",
      bounceRate: 32.5,
      conversions: 234,
    },
    {
      path: "/features",
      title: "Features",
      views: 6540,
      uniqueVisitors: 2456,
      avgTime: "3m 28s",
      bounceRate: 41.3,
      conversions: 98,
    },
    {
      path: "/about",
      title: "About",
      views: 4320,
      uniqueVisitors: 1890,
      avgTime: "2m 56s",
      bounceRate: 45.8,
      conversions: 42,
    },
    {
      path: "/contact",
      title: "Contact",
      views: 3210,
      uniqueVisitors: 1234,
      avgTime: "2m 15s",
      bounceRate: 52.1,
      conversions: 67,
    },
    {
      path: "/blog",
      title: "Blog",
      views: 2890,
      uniqueVisitors: 1056,
      avgTime: "5m 34s",
      bounceRate: 28.9,
      conversions: 45,
    },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Page Analytics</h1>
        <p className="text-gray-400">Detailed performance metrics for each page</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <p className="text-sm text-gray-400">Total Pages</p>
          <p className="text-3xl font-bold text-white mt-1">{pages.length}</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <p className="text-sm text-gray-400">Total Views</p>
          <p className="text-3xl font-bold text-white mt-1">
            {pages.reduce((sum, p) => sum + p.views, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <p className="text-sm text-gray-400">Unique Visitors</p>
          <p className="text-3xl font-bold text-white mt-1">
            {pages.reduce((sum, p) => sum + p.uniqueVisitors, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <p className="text-sm text-gray-400">Total Conversions</p>
          <p className="text-3xl font-bold text-white mt-1">
            {pages.reduce((sum, p) => sum + p.conversions, 0)}
          </p>
        </div>
      </div>

      {/* Pages Table */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
          <div className="col-span-3">Page</div>
          <div className="col-span-2">Views</div>
          <div className="col-span-2">Visitors</div>
          <div className="col-span-2">Avg Time</div>
          <div className="col-span-2">Bounce Rate</div>
          <div className="col-span-1">Actions</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/10">
          {pages.map((page, i) => (
            <div
              key={i}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
            >
              {/* Page Info */}
              <div className="col-span-3 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <FileText className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <p className="text-white font-medium">{page.title}</p>
                  <p className="text-sm text-gray-400">{page.path}</p>
                </div>
              </div>

              {/* Views */}
              <div className="col-span-2 flex items-center">
                <div>
                  <p className="text-white font-medium">{page.views.toLocaleString()}</p>
                  <div className="flex items-center gap-1 text-xs text-green-400">
                    <TrendingUp className="w-3 h-3" />
                    <span>+12%</span>
                  </div>
                </div>
              </div>

              {/* Unique Visitors */}
              <div className="col-span-2 flex items-center">
                <p className="text-white">{page.uniqueVisitors.toLocaleString()}</p>
              </div>

              {/* Avg Time */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400">
                  <Clock className="w-4 h-4" />
                  <span>{page.avgTime}</span>
                </div>
              </div>

              {/* Bounce Rate */}
              <div className="col-span-2 flex items-center">
                <div className="w-full">
                  <p className={`text-sm mb-1 ${page.bounceRate > 45 ? 'text-red-400' : 'text-green-400'}`}>
                    {page.bounceRate}%
                  </p>
                  <div className="w-full bg-gray-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${page.bounceRate > 45 ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${page.bounceRate}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="col-span-1 flex items-center justify-end">
                <button className="text-blue-400 hover:text-blue-300 p-2 rounded hover:bg-blue-500/10 transition">
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Page Performance Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Top Converting Pages</h3>
          <div className="space-y-4">
            {pages
              .sort((a, b) => b.conversions - a.conversions)
              .slice(0, 5)
              .map((page, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="flex-1">
                    <p className="text-white text-sm">{page.title}</p>
                    <p className="text-xs text-gray-400">{page.conversions} conversions</p>
                  </div>
                  <div className="w-32">
                    <div className="bg-black rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full"
                        style={{ width: `${(page.conversions / pages[0].conversions) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Longest Session Duration</h3>
          <div className="space-y-4">
            {pages
              .sort((a, b) => {
                const aTime = parseInt(a.avgTime.split('m')[0]) * 60 + parseInt(a.avgTime.split('m')[1]);
                const bTime = parseInt(b.avgTime.split('m')[0]) * 60 + parseInt(b.avgTime.split('m')[1]);
                return bTime - aTime;
              })
              .slice(0, 5)
              .map((page, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="flex-1">
                    <p className="text-white text-sm">{page.title}</p>
                    <p className="text-xs text-gray-400">{page.avgTime} average</p>
                  </div>
                  <div className="w-32">
                    <div className="bg-black rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                        style={{ width: `${(parseInt(page.avgTime.split('m')[0]) / 6) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
