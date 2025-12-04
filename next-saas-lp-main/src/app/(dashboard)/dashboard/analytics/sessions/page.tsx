"use client";

import { Users, Clock, Globe, Monitor, Smartphone, Play } from "lucide-react";

export default function AnalyticsSessionsPage() {
  const sessionStats = {
    totalSessions: 8945,
    avgDuration: "3m 24s",
    bounceRate: 42.3,
    pagesPerSession: 3.8,
  };

  const sessions = [
    {
      id: "sess_12345",
      user: "Anonymous",
      location: "San Francisco, CA",
      device: "Desktop",
      browser: "Chrome",
      duration: "5m 34s",
      pages: 7,
      startTime: "2 hours ago",
      status: "active",
    },
    {
      id: "sess_12346",
      user: "user@example.com",
      location: "New York, NY",
      device: "Mobile",
      browser: "Safari",
      duration: "3m 12s",
      pages: 4,
      startTime: "3 hours ago",
      status: "completed",
    },
    {
      id: "sess_12347",
      user: "Anonymous",
      location: "London, UK",
      device: "Tablet",
      browser: "Firefox",
      duration: "4m 45s",
      pages: 5,
      startTime: "4 hours ago",
      status: "completed",
    },
    {
      id: "sess_12348",
      user: "john@company.com",
      location: "Toronto, Canada",
      device: "Desktop",
      browser: "Edge",
      duration: "6m 18s",
      pages: 9,
      startTime: "5 hours ago",
      status: "completed",
    },
  ];

  const deviceBreakdown = [
    { device: "Desktop", sessions: 4523, percentage: 50.5 },
    { device: "Mobile", sessions: 3578, percentage: 40.0 },
    { device: "Tablet", sessions: 844, percentage: 9.5 },
  ];

  const browserBreakdown = [
    { browser: "Chrome", sessions: 5367, percentage: 60.0 },
    { browser: "Safari", sessions: 1789, percentage: 20.0 },
    { browser: "Firefox", sessions: 1342, percentage: 15.0 },
    { browser: "Edge", sessions: 447, percentage: 5.0 },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Session Analytics</h1>
        <p className="text-gray-400">Track user sessions and behavior patterns</p>
      </div>

      {/* Session Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="p-3 rounded-full bg-blue-500/20 w-fit mb-4">
            <Users className="w-6 h-6 text-blue-400" />
          </div>
          <p className="text-sm text-gray-400">Total Sessions</p>
          <p className="text-3xl font-bold text-white mt-1">{sessionStats.totalSessions.toLocaleString()}</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="p-3 rounded-full bg-purple-500/20 w-fit mb-4">
            <Clock className="w-6 h-6 text-purple-400" />
          </div>
          <p className="text-sm text-gray-400">Avg Duration</p>
          <p className="text-3xl font-bold text-white mt-1">{sessionStats.avgDuration}</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="p-3 rounded-full bg-orange-500/20 w-fit mb-4">
            <Globe className="w-6 h-6 text-orange-400" />
          </div>
          <p className="text-sm text-gray-400">Bounce Rate</p>
          <p className="text-3xl font-bold text-white mt-1">{sessionStats.bounceRate}%</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="p-3 rounded-full bg-green-500/20 w-fit mb-4">
            <Play className="w-6 h-6 text-green-400" />
          </div>
          <p className="text-sm text-gray-400">Pages/Session</p>
          <p className="text-3xl font-bold text-white mt-1">{sessionStats.pagesPerSession}</p>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white">Recent Sessions</h3>
        </div>

        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
          <div className="col-span-2">User</div>
          <div className="col-span-2">Location</div>
          <div className="col-span-2">Device</div>
          <div className="col-span-2">Duration</div>
          <div className="col-span-1">Pages</div>
          <div className="col-span-2">Started</div>
          <div className="col-span-1">Status</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/10">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
            >
              {/* User */}
              <div className="col-span-2 flex items-center">
                <p className="text-white text-sm truncate">{session.user}</p>
              </div>

              {/* Location */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Globe className="w-3 h-3" />
                  <span className="truncate">{session.location}</span>
                </div>
              </div>

              {/* Device */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  {session.device === "Desktop" ? (
                    <Monitor className="w-3 h-3" />
                  ) : (
                    <Smartphone className="w-3 h-3" />
                  )}
                  <span>{session.device} • {session.browser}</span>
                </div>
              </div>

              {/* Duration */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Clock className="w-3 h-3" />
                  <span>{session.duration}</span>
                </div>
              </div>

              {/* Pages */}
              <div className="col-span-1 flex items-center">
                <p className="text-white text-sm">{session.pages}</p>
              </div>

              {/* Started */}
              <div className="col-span-2 flex items-center">
                <p className="text-gray-400 text-sm">{session.startTime}</p>
              </div>

              {/* Status */}
              <div className="col-span-1 flex items-center">
                <span className={`text-xs px-2 py-1 rounded ${
                  session.status === "active" 
                    ? "bg-green-500/20 text-green-400" 
                    : "bg-gray-500/20 text-gray-400"
                }`}>
                  {session.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Device & Browser Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Breakdown */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Device Breakdown</h3>
          <div className="space-y-4">
            {deviceBreakdown.map((item, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {item.device === "Desktop" ? (
                      <Monitor className="w-4 h-4 text-blue-400" />
                    ) : item.device === "Mobile" ? (
                      <Smartphone className="w-4 h-4 text-purple-400" />
                    ) : (
                      <Monitor className="w-4 h-4 text-green-400" />
                    )}
                    <span className="text-white text-sm">{item.device}</span>
                  </div>
                  <span className="text-gray-400 text-sm">{item.sessions.toLocaleString()} ({item.percentage}%)</span>
                </div>
                <div className="bg-black rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Browser Breakdown */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Browser Breakdown</h3>
          <div className="space-y-4">
            {browserBreakdown.map((item, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm">{item.browser}</span>
                  <span className="text-gray-400 text-sm">{item.sessions.toLocaleString()} ({item.percentage}%)</span>
                </div>
                <div className="bg-black rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
