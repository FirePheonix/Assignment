"use client";

import {
  Users,
  Building2,
  DollarSign,
  TrendingUp,
  Calendar,
  Activity,
  Plus,
  FileText,
} from "lucide-react";

export default function CRMDashboardPage() {
  const metrics = {
    totalContacts: 1234,
    newContactsWeek: 45,
    totalCompanies: 156,
    newCompaniesWeek: 8,
    activeDeals: 32,
    dealsClosedWeek: 5,
    pipelineValue: 487500,
    weightedValue: 243750,
    tasksToday: 12,
  };

  const recentActivities = [
    { type: "contact", action: "New contact added", name: "John Smith", time: "2 hours ago" },
    { type: "deal", action: "Deal closed", name: "Acme Corp - $50K", time: "4 hours ago" },
    { type: "company", action: "Company updated", name: "Tech Solutions Inc", time: "6 hours ago" },
    { type: "task", action: "Task completed", name: "Follow-up call", time: "8 hours ago" },
  ];

  const upcomingTasks = [
    { title: "Follow-up with John Smith", due: "Today, 2:00 PM", priority: "high" },
    { title: "Prepare proposal for Acme Corp", due: "Today, 4:30 PM", priority: "high" },
    { title: "Team meeting", due: "Tomorrow, 10:00 AM", priority: "medium" },
    { title: "Review contracts", due: "Dec 22, 2025", priority: "low" },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">CRM Dashboard</h1>
        <p className="text-gray-400">Customer Relationship Management Overview</p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-8">
        <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition">
          <Plus className="w-4 h-4" />
          Add Contact
        </button>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition">
          <Plus className="w-4 h-4" />
          Add Company
        </button>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition">
          <FileText className="w-4 h-4" />
          Reports
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-full bg-blue-500/20">
              <Users className="w-6 h-6 text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-400">Total Contacts</p>
              <p className="text-2xl font-bold text-white">{metrics.totalContacts}</p>
            </div>
          </div>
          <span className="text-green-400 text-sm">+{metrics.newContactsWeek} this week</span>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-full bg-indigo-500/20">
              <Building2 className="w-6 h-6 text-indigo-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-400">Total Companies</p>
              <p className="text-2xl font-bold text-white">{metrics.totalCompanies}</p>
            </div>
          </div>
          <span className="text-green-400 text-sm">+{metrics.newCompaniesWeek} this week</span>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-full bg-purple-500/20">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-400">Active Deals</p>
              <p className="text-2xl font-bold text-white">{metrics.activeDeals}</p>
            </div>
          </div>
          <span className="text-green-400 text-sm">{metrics.dealsClosedWeek} closed this week</span>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-full bg-green-500/20">
              <DollarSign className="w-6 h-6 text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-400">Pipeline Value</p>
              <p className="text-2xl font-bold text-white">${(metrics.pipelineValue / 1000).toFixed(0)}K</p>
            </div>
          </div>
          <span className="text-blue-400 text-sm">${(metrics.weightedValue / 1000).toFixed(0)}K weighted</span>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-full bg-orange-500/20">
              <Calendar className="w-6 h-6 text-orange-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-400">Tasks Today</p>
              <p className="text-2xl font-bold text-white">{metrics.tasksToday}</p>
            </div>
          </div>
          <span className="text-gray-400 text-sm">3 overdue</span>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Recent Activity
          </h3>
          <div className="space-y-4">
            {recentActivities.map((activity, i) => (
              <div key={i} className="flex items-start gap-3 pb-4 border-b border-white/10 last:border-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  activity.type === "contact" ? "bg-blue-500/20 text-blue-400" :
                  activity.type === "deal" ? "bg-green-500/20 text-green-400" :
                  activity.type === "company" ? "bg-indigo-500/20 text-indigo-400" :
                  "bg-orange-500/20 text-orange-400"
                }`}>
                  {activity.type === "contact" && <Users className="w-4 h-4" />}
                  {activity.type === "deal" && <DollarSign className="w-4 h-4" />}
                  {activity.type === "company" && <Building2 className="w-4 h-4" />}
                  {activity.type === "task" && <Calendar className="w-4 h-4" />}
                </div>
                <div className="flex-1">
                  <p className="text-white text-sm">{activity.action}</p>
                  <p className="text-gray-400 text-xs">{activity.name}</p>
                </div>
                <span className="text-xs text-gray-500">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Tasks */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Upcoming Tasks
          </h3>
          <div className="space-y-3">
            {upcomingTasks.map((task, i) => (
              <div key={i} className="bg-black border border-white/10 rounded-lg p-4 hover:border-purple-500/50 transition">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-white text-sm font-medium">{task.title}</p>
                  <span className={`text-xs px-2 py-1 rounded ${
                    task.priority === "high" ? "bg-red-500/20 text-red-400" :
                    task.priority === "medium" ? "bg-yellow-500/20 text-yellow-400" :
                    "bg-gray-500/20 text-gray-400"
                  }`}>
                    {task.priority}
                  </span>
                </div>
                <p className="text-xs text-gray-400">{task.due}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
