"use client";

import { Building2, Search, Plus, Mail, Phone, MapPin, Users } from "lucide-react";

export default function CRMCompaniesPage() {
  const companies = [
    {
      id: 1,
      name: "Acme Corporation",
      industry: "Technology",
      employees: 250,
      revenue: "$5M-$10M",
      website: "acmecorp.com",
      email: "contact@acmecorp.com",
      phone: "+1 (555) 123-4567",
      location: "San Francisco, CA",
      contacts: 8,
      deals: 3,
      status: "active",
    },
    {
      id: 2,
      name: "Tech Solutions Inc",
      industry: "Software",
      employees: 120,
      revenue: "$2M-$5M",
      website: "techsolutions.com",
      email: "hello@techsolutions.com",
      phone: "+1 (555) 987-6543",
      location: "New York, NY",
      contacts: 5,
      deals: 2,
      status: "active",
    },
    {
      id: 3,
      name: "Digital Ventures LLC",
      industry: "Marketing",
      employees: 45,
      revenue: "$1M-$2M",
      website: "digitalventures.com",
      email: "info@digitalventures.com",
      phone: "+1 (555) 456-7890",
      location: "Austin, TX",
      contacts: 3,
      deals: 1,
      status: "prospect",
    },
  ];

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Companies</h1>
        <p className="text-gray-400">Manage your company relationships</p>
      </div>

      {/* Actions Bar */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search companies..."
            className="w-full pl-10 pr-4 py-3 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
          <option>All Industries</option>
          <option>Technology</option>
          <option>Software</option>
          <option>Marketing</option>
        </select>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Company
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Total Companies</p>
          <p className="text-2xl font-bold text-white mt-1">156</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Active Clients</p>
          <p className="text-2xl font-bold text-green-400 mt-1">89</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">Prospects</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">42</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
          <p className="text-sm text-gray-400">New This Month</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">12</p>
        </div>
      </div>

      {/* Companies Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {companies.map((company) => (
          <div
            key={company.id}
            className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition cursor-pointer"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{company.name}</h3>
                  <p className="text-sm text-gray-400">{company.industry}</p>
                </div>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${
                company.status === "active" 
                  ? "bg-green-500/20 text-green-400" 
                  : "bg-blue-500/20 text-blue-400"
              }`}>
                {company.status}
              </span>
            </div>

            {/* Details */}
            <div className="space-y-2 mb-4 text-sm">
              <div className="flex items-center gap-2 text-gray-400">
                <Users className="w-4 h-4" />
                <span>{company.employees} employees</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <Mail className="w-4 h-4" />
                <span className="truncate">{company.email}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <Phone className="w-4 h-4" />
                <span>{company.phone}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <MapPin className="w-4 h-4" />
                <span>{company.location}</span>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 py-3 border-t border-white/10">
              <div className="text-center">
                <p className="text-xl font-bold text-white">{company.contacts}</p>
                <p className="text-xs text-gray-400">Contacts</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-white">{company.deals}</p>
                <p className="text-xs text-gray-400">Deals</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-white">{company.revenue}</p>
                <p className="text-xs text-gray-400">Revenue</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-4">
              <button className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg text-sm font-medium transition">
                View Details
              </button>
              <button className="px-4 bg-white/5 hover:bg-white/10 text-white py-2 rounded-lg text-sm transition">
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
