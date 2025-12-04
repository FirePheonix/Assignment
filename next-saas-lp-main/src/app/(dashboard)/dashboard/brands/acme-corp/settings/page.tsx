"use client";

import { Building2, Twitter, Instagram, Globe, Settings, Trash2 } from "lucide-react";

export default function BrandSettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Brand Settings</h1>
        <p className="text-gray-400 mt-1">
          Manage your brand information and connections
        </p>
      </div>

      {/* Brand Information */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Brand Information</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Brand Name</label>
            <input
              type="text"
              defaultValue="Acme Corporation"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              rows={3}
              defaultValue="Leading technology solutions provider"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Website</label>
            <input
              type="url"
              defaultValue="https://acme.com"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <button className="bg-white/5 border border-white/10 hover:bg-white/10 px-6 py-2 rounded-lg text-sm transition-colors">
              Cancel
            </button>
            <button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-2 rounded-lg text-sm transition-opacity">
              Save Changes
            </button>
          </div>
        </div>
      </div>

      {/* Social Connections */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Social Media Connections</h2>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div className="flex items-center gap-3">
              <Twitter className="w-5 h-5 text-blue-400" />
              <div>
                <div className="font-medium">Twitter</div>
                <div className="text-sm text-gray-400">@acmecorp</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-xs">
                Connected
              </span>
              <button className="text-red-400 hover:text-red-300 p-2">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div className="flex items-center gap-3">
              <Instagram className="w-5 h-5 text-pink-400" />
              <div>
                <div className="font-medium">Instagram</div>
                <div className="text-sm text-gray-400">@acmecorp</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-xs">
                Connected
              </span>
              <button className="text-red-400 hover:text-red-300 p-2">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
        <h3 className="text-lg font-bold text-red-400 mb-2">Danger Zone</h3>
        <p className="text-sm text-gray-400 mb-4">
          Deleting this brand will remove all associated content and connections. This action cannot be undone.
        </p>
        <button className="bg-red-500/20 text-red-400 hover:bg-red-500/30 px-4 py-2 rounded-lg text-sm transition-colors">
          Delete Brand
        </button>
      </div>
    </div>
  );
}
