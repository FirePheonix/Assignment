"use client";

import { Twitter, Instagram, BarChart3, Settings } from "lucide-react";
import Link from "next/link";

export default function BrandDetailPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Acme Corporation</h1>
          <p className="text-gray-400 mt-1">
            Leading technology solutions provider
          </p>
        </div>
        <Link
          href="/dashboard/brands/acme-corp/settings"
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <Settings className="w-5 h-5 text-gray-400" />
        </Link>
      </div>

      {/* Quick Links Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link
          href="/dashboard/brands/acme-corp/twitter"
          className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
              <Twitter className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Twitter</h3>
              <p className="text-sm text-gray-400">Manage tweets & queue</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">156 posts</span>
            <span className="text-green-400">Connected</span>
          </div>
        </Link>

        <Link
          href="/dashboard/brands/acme-corp/instagram"
          className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-pink-500/20 rounded-lg group-hover:bg-pink-500/30 transition-colors">
              <Instagram className="w-6 h-6 text-pink-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Instagram</h3>
              <p className="text-sm text-gray-400">Manage posts & reels</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">89 posts</span>
            <span className="text-green-400">Connected</span>
          </div>
        </Link>

        <Link
          href="/dashboard/brands/acme-corp/analytics"
          className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-purple-500/20 rounded-lg group-hover:bg-purple-500/30 transition-colors">
              <BarChart3 className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Analytics</h3>
              <p className="text-sm text-gray-400">View performance</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">12.5K reach</span>
            <span className="text-blue-400">View stats</span>
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">245</div>
          <div className="text-sm text-gray-400">Total Posts</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">12.5K</div>
          <div className="text-sm text-gray-400">Total Reach</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">3.2K</div>
          <div className="text-sm text-gray-400">Followers</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">4.8%</div>
          <div className="text-sm text-gray-400">Engagement</div>
        </div>
      </div>
    </div>
  );
}
