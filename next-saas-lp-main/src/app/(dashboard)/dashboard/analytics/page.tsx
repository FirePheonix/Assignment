"use client";

import { BarChart3, Users, Eye, TrendingUp, Clock, Globe } from "lucide-react";

export default function AnalyticsDashboardPage() {
  const stats = {
    totalPageViews: 45230,
    uniqueVisitors: 12456,
    avgSessionDuration: "3m 24s",
    bounceRate: 42.3,
    conversionRate: 3.8,
    totalEvents: 8945,
  };

  const topPages = [
    { path: "/", views: 12340, visitors: 4521 },
    { path: "/pricing", views: 8760, visitors: 3210 },
    { path: "/features", views: 6540, visitors: 2456 },
    { path: "/about", views: 4320, visitors: 1890 },
    { path: "/contact", views: 3210, visitors: 1234 },
  ];

  const recentSessions = [
    { location: "United States", sessions: 5234, duration: "4m 12s" },
    { location: "United Kingdom", sessions: 2341, duration: "3m 45s" },
    { location: "Canada", sessions: 1876, duration: "3m 18s" },
    { location: "Australia", sessions: 1234, duration: "2m 56s" },
    { location: "Germany", sessions: 987, duration: "3m 02s" },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
        <p className="text-gray-400">Track your website performance and user behavior</p>
      </div>

      {/* Date Range Selector */}
      <div className="flex items-center gap-3 mb-8">
        <select className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
          <option>This year</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-blue-500/20">
              <Eye className="w-6 h-6 text-blue-400" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-sm text-gray-400">Total Page Views</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.totalPageViews.toLocaleString()}</p>
          <p className="text-sm text-green-400 mt-2">+12.5% from last period</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-purple-500/20">
              <Users className="w-6 h-6 text-purple-400" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-sm text-gray-400">Unique Visitors</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.uniqueVisitors.toLocaleString()}</p>
          <p className="text-sm text-green-400 mt-2">+8.3% from last period</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-orange-500/20">
              <Clock className="w-6 h-6 text-orange-400" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-sm text-gray-400">Avg Session Duration</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.avgSessionDuration}</p>
          <p className="text-sm text-green-400 mt-2">+5.2% from last period</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-red-500/20">
              <BarChart3 className="w-6 h-6 text-red-400" />
            </div>
          </div>
          <p className="text-sm text-gray-400">Bounce Rate</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.bounceRate}%</p>
          <p className="text-sm text-red-400 mt-2">-2.1% from last period</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-green-500/20">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-sm text-gray-400">Conversion Rate</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.conversionRate}%</p>
          <p className="text-sm text-green-400 mt-2">+0.4% from last period</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-indigo-500/20">
              <Globe className="w-6 h-6 text-indigo-400" />
            </div>
          </div>
          <p className="text-sm text-gray-400">Total Events</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.totalEvents.toLocaleString()}</p>
          <p className="text-sm text-green-400 mt-2">+15.7% from last period</p>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Pages */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Top Pages</h3>
          <div className="space-y-4">
            {topPages.map((page, i) => (
              <div key={i} className="flex items-center justify-between pb-4 border-b border-white/10 last:border-0">
                <div className="flex-1">
                  <p className="text-white font-medium mb-1">{page.path}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{page.views.toLocaleString()} views</span>
                    <span>{page.visitors.toLocaleString()} visitors</span>
                  </div>
                </div>
                <div className="w-24">
                  <div className="bg-black rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                      style={{ width: `${(page.views / topPages[0].views) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Locations */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Top Locations</h3>
          <div className="space-y-4">
            {recentSessions.map((session, i) => (
              <div key={i} className="flex items-center justify-between pb-4 border-b border-white/10 last:border-0">
                <div className="flex-1">
                  <p className="text-white font-medium mb-1">{session.location}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{session.sessions.toLocaleString()} sessions</span>
                    <span>{session.duration} avg</span>
                  </div>
                </div>
                <div className="w-24">
                  <div className="bg-black rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full"
                      style={{ width: `${(session.sessions / recentSessions[0].sessions) * 100}%` }}
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
