"use client";

import { Zap, MousePointer, Eye, ShoppingCart, Mail } from "lucide-react";

export default function AnalyticsEventsPage() {
  const eventCategories = [
    { name: "Button Clicks", count: 3456, icon: MousePointer, color: "blue" },
    { name: "Page Views", count: 12340, icon: Eye, color: "purple" },
    { name: "Form Submissions", count: 456, icon: Mail, color: "green" },
    { name: "Purchases", count: 234, icon: ShoppingCart, color: "orange" },
  ];

  const events = [
    {
      name: "CTA Click - Get Started",
      category: "Button Clicks",
      count: 1234,
      uniqueUsers: 890,
      avgValue: 0,
      timestamp: "2 hours ago",
    },
    {
      name: "Form Submit - Contact",
      category: "Form Submissions",
      count: 234,
      uniqueUsers: 189,
      avgValue: 0,
      timestamp: "3 hours ago",
    },
    {
      name: "Purchase - Pro Plan",
      category: "Purchases",
      count: 89,
      uniqueUsers: 89,
      avgValue: 49.99,
      timestamp: "5 hours ago",
    },
    {
      name: "Video Play - Demo",
      category: "Engagement",
      count: 567,
      uniqueUsers: 423,
      avgValue: 0,
      timestamp: "6 hours ago",
    },
    {
      name: "Download - Whitepaper",
      category: "Downloads",
      count: 345,
      uniqueUsers: 298,
      avgValue: 0,
      timestamp: "8 hours ago",
    },
  ];

  const topEvents = [
    { name: "Page View", count: 12340 },
    { name: "Click CTA", count: 3456 },
    { name: "Scroll 50%", count: 2890 },
    { name: "Video Play", count: 1234 },
    { name: "Form Submit", count: 890 },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Event Analytics</h1>
        <p className="text-gray-400">Track user interactions and custom events</p>
      </div>

      {/* Event Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {eventCategories.map((category, i) => {
          const Icon = category.icon;
          return (
            <div key={i} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <div className={`p-3 rounded-full bg-${category.color}-500/20 w-fit mb-4`}>
                <Icon className={`w-6 h-6 text-${category.color}-400`} />
              </div>
              <p className="text-sm text-gray-400">{category.name}</p>
              <p className="text-3xl font-bold text-white mt-1">{category.count.toLocaleString()}</p>
            </div>
          );
        })}
      </div>

      {/* Recent Events */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Recent Events
          </h3>
        </div>

        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
          <div className="col-span-4">Event Name</div>
          <div className="col-span-2">Category</div>
          <div className="col-span-2">Total Count</div>
          <div className="col-span-2">Unique Users</div>
          <div className="col-span-2">Avg Value</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/10">
          {events.map((event, i) => (
            <div
              key={i}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
            >
              {/* Event Name */}
              <div className="col-span-4 flex flex-col justify-center">
                <p className="text-white font-medium">{event.name}</p>
                <p className="text-sm text-gray-400">{event.timestamp}</p>
              </div>

              {/* Category */}
              <div className="col-span-2 flex items-center">
                <span className="bg-purple-500/20 text-purple-400 text-xs px-3 py-1 rounded">
                  {event.category}
                </span>
              </div>

              {/* Total Count */}
              <div className="col-span-2 flex items-center">
                <p className="text-white font-medium">{event.count.toLocaleString()}</p>
              </div>

              {/* Unique Users */}
              <div className="col-span-2 flex items-center">
                <p className="text-gray-400">{event.uniqueUsers.toLocaleString()}</p>
              </div>

              {/* Avg Value */}
              <div className="col-span-2 flex items-center">
                <p className={`font-medium ${event.avgValue > 0 ? 'text-green-400' : 'text-gray-400'}`}>
                  {event.avgValue > 0 ? `$${event.avgValue}` : '-'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Events Chart */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Top Events (Last 7 Days)</h3>
          <div className="space-y-4">
            {topEvents.map((event, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-8 text-gray-400 text-sm">{i + 1}</div>
                <div className="flex-1">
                  <p className="text-white text-sm mb-1">{event.name}</p>
                  <div className="bg-black rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                      style={{ width: `${(event.count / topEvents[0].count) * 100}%` }}
                    />
                  </div>
                </div>
                <p className="text-gray-400 text-sm w-20 text-right">{event.count.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Event Timeline */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Event Timeline</h3>
          <div className="space-y-4">
            {events.slice(0, 5).map((event, i) => (
              <div key={i} className="flex items-start gap-3 pb-4 border-b border-white/10 last:border-0">
                <div className="w-2 h-2 rounded-full bg-purple-500 mt-2" />
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">{event.name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {event.count} events • {event.uniqueUsers} users
                  </p>
                </div>
                <span className="text-xs text-gray-500">{event.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
