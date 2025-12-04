"use client";

import { UserCircle, Search, Plus, Mail, Phone, Building2, Tag } from "lucide-react";

export default function CRMContactsPage() {
  const contacts = [
    {
      id: 1,
      name: "John Smith",
      title: "CEO",
      company: "Acme Corporation",
      email: "john.smith@acmecorp.com",
      phone: "+1 (555) 123-4567",
      tags: ["Decision Maker", "High Priority"],
      lastContact: "2 days ago",
      deals: 2,
      status: "active",
    },
    {
      id: 2,
      name: "Sarah Johnson",
      title: "CTO",
      company: "Tech Solutions Inc",
      email: "sarah.j@techsolutions.com",
      phone: "+1 (555) 987-6543",
      tags: ["Technical Lead"],
      lastContact: "1 week ago",
      deals: 1,
      status: "active",
    },
    {
      id: 3,
      name: "Michael Chen",
      title: "Marketing Director",
      company: "Digital Ventures LLC",
      email: "m.chen@digitalventures.com",
      phone: "+1 (555) 456-7890",
      tags: ["Prospect"],
      lastContact: "3 days ago",
      deals: 0,
      status: "prospect",
    },
    {
      id: 4,
      name: "Emily Rodriguez",
      title: "VP of Sales",
      company: "Growth Partners",
      email: "emily.r@growthpartners.com",
      phone: "+1 (555) 234-5678",
      tags: ["Decision Maker", "Warm Lead"],
      lastContact: "5 days ago",
      deals: 3,
      status: "active",
    },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Contacts</h1>
        <p className="text-gray-400">Manage your contact relationships</p>
      </div>

      {/* Actions Bar */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search contacts..."
            className="w-full pl-10 pr-4 py-3 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
          <option>All Contacts</option>
          <option>Active</option>
          <option>Prospects</option>
          <option>Inactive</option>
        </select>
        <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Contact
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Total Contacts</p>
          <p className="text-2xl font-bold text-white mt-1">1,234</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Active Contacts</p>
          <p className="text-2xl font-bold text-green-400 mt-1">856</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">New This Week</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">45</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Need Follow-up</p>
          <p className="text-2xl font-bold text-orange-400 mt-1">23</p>
        </div>
      </div>

      {/* Contacts List */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
          <div className="col-span-3">Contact</div>
          <div className="col-span-2">Company</div>
          <div className="col-span-2">Contact Info</div>
          <div className="col-span-2">Tags</div>
          <div className="col-span-2">Last Contact</div>
          <div className="col-span-1">Actions</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/10">
          {contacts.map((contact) => (
            <div
              key={contact.id}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
            >
              {/* Contact Name & Title */}
              <div className="col-span-3 flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <UserCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-white font-medium">{contact.name}</p>
                  <p className="text-sm text-gray-400">{contact.title}</p>
                </div>
              </div>

              {/* Company */}
              <div className="col-span-2 flex items-center">
                <div className="flex items-center gap-2 text-gray-400">
                  <Building2 className="w-4 h-4" />
                  <span className="text-sm">{contact.company}</span>
                </div>
              </div>

              {/* Contact Info */}
              <div className="col-span-2 flex flex-col justify-center gap-1">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Mail className="w-3 h-3" />
                  <span className="truncate">{contact.email}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Phone className="w-3 h-3" />
                  <span>{contact.phone}</span>
                </div>
              </div>

              {/* Tags */}
              <div className="col-span-2 flex items-center">
                <div className="flex flex-wrap gap-1">
                  {contact.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="bg-purple-500/20 text-purple-400 text-xs px-2 py-1 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Last Contact */}
              <div className="col-span-2 flex items-center">
                <div>
                  <p className="text-sm text-gray-400">{contact.lastContact}</p>
                  <p className="text-xs text-gray-500">{contact.deals} active deals</p>
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
          <p className="text-sm text-gray-400">Showing 1-4 of 1,234 contacts</p>
          <div className="flex items-center gap-2">
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">
              Previous
            </button>
            <button className="bg-purple-600 text-white px-3 py-1 rounded">1</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">2</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">3</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
