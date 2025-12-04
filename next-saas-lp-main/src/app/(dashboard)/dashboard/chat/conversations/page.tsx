"use client";

import { Search, MessageSquare, Users, Clock, Filter } from "lucide-react";

export default function ConversationsPage() {
  const conversations = [
    {
      id: 1,
      name: "John Smith",
      type: "direct",
      participants: 2,
      lastMessage: "Thanks for the update!",
      lastActivity: "2 minutes ago",
      unread: 2,
      avatar: "JS",
      status: "active",
    },
    {
      id: 2,
      name: "Sarah Johnson",
      type: "direct",
      participants: 2,
      lastMessage: "Can we schedule a call?",
      lastActivity: "1 hour ago",
      unread: 0,
      avatar: "SJ",
      status: "active",
    },
    {
      id: 3,
      name: "Marketing Team",
      type: "group",
      participants: 8,
      lastMessage: "New campaign draft ready for review",
      lastActivity: "3 hours ago",
      unread: 5,
      avatar: "MT",
      status: "active",
    },
    {
      id: 4,
      name: "Sales Pipeline Discussion",
      type: "group",
      participants: 6,
      lastMessage: "Let's sync up on Q4 targets",
      lastActivity: "5 hours ago",
      unread: 12,
      avatar: "SP",
      status: "active",
    },
    {
      id: 5,
      name: "Mike Chen",
      type: "direct",
      participants: 2,
      lastMessage: "Perfect, thanks!",
      lastActivity: "Yesterday",
      unread: 0,
      avatar: "MC",
      status: "archived",
    },
    {
      id: 6,
      name: "Product Development",
      type: "group",
      participants: 12,
      lastMessage: "Sprint planning for next week",
      lastActivity: "Yesterday",
      unread: 3,
      avatar: "PD",
      status: "active",
    },
  ];

  const stats = {
    total: conversations.length,
    active: conversations.filter(c => c.status === "active").length,
    unread: conversations.reduce((sum, c) => sum + c.unread, 0),
    groups: conversations.filter(c => c.type === "group").length,
  };

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">All Conversations</h1>
        <p className="text-gray-400">Manage and browse all your conversations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Total Conversations</p>
            <MessageSquare className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">{stats.total}</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Active</p>
            <Clock className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">{stats.active}</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Unread Messages</p>
            <MessageSquare className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-3xl font-bold text-white">{stats.unread}</p>
        </div>

        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Group Chats</p>
            <Users className="w-5 h-5 text-orange-400" />
          </div>
          <p className="text-3xl font-bold text-white">{stats.groups}</p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            className="w-full pl-10 pr-4 py-3 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
          <option>All Types</option>
          <option>Direct Messages</option>
          <option>Group Chats</option>
        </select>
        <button className="bg-white/5 hover:bg-white/10 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2">
          <Filter className="w-4 h-4" />
          More Filters
        </button>
      </div>

      {/* Conversations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition cursor-pointer"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                  {conv.avatar}
                </div>
                <div>
                  <h3 className="font-semibold text-white">{conv.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      conv.type === "group" 
                        ? "bg-blue-500/20 text-blue-400" 
                        : "bg-purple-500/20 text-purple-400"
                    }`}>
                      {conv.type}
                    </span>
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {conv.participants}
                    </span>
                  </div>
                </div>
              </div>
              {conv.unread > 0 && (
                <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded-full">
                  {conv.unread}
                </span>
              )}
            </div>

            {/* Last Message */}
            <div className="mb-4">
              <p className="text-sm text-gray-400 line-clamp-2">{conv.lastMessage}</p>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-gray-400 pt-4 border-t border-white/10">
              <div className="flex items-center gap-2">
                <Clock className="w-3 h-3" />
                <span>{conv.lastActivity}</span>
              </div>
              <button className="text-blue-400 hover:text-blue-300 font-medium">
                Open Chat →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
