"use client";

import { useState } from "react";
import { BarChart3, TrendingUp, Users, Activity, Image, Grid3x3, X } from "lucide-react";
import { WorkspaceMediaGallery } from "@/components/WorkspaceMediaGallery";
import { type WorkspaceMediaItem } from "@/hooks/use-workspace-media";

export default function DashboardPage() {
  const [showMediaGallery, setShowMediaGallery] = useState(false);
  const [selectedMedia, setSelectedMedia] = useState<WorkspaceMediaItem | null>(null);

  const stats = [
    {
      name: "Total Videos",
      value: "1,234",
      change: "+12%",
      icon: Activity,
    },
    {
      name: "Views This Month",
      value: "45.2K",
      change: "+23%",
      icon: BarChart3,
    },
    {
      name: "Active Projects",
      value: "8",
      change: "+2",
      icon: Users,
    },
    {
      name: "Engagement Rate",
      value: "68%",
      change: "+5%",
      icon: TrendingUp,
    },
  ];



  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-400 mt-1">
          Welcome back! Here's what's happening with your projects.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.name}
              className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Icon className="w-5 h-5 text-purple-400" />
                </div>
                <span className="text-green-400 text-sm font-medium">
                  {stat.change}
                </span>
              </div>
              <h3 className="text-2xl font-bold mb-1">{stat.value}</h3>
              <p className="text-gray-400 text-sm">{stat.name}</p>
            </div>
          );
        })}
      </div>



      {/* Media Feed */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold">Your Media Feed</h2>
            <p className="text-gray-400 text-sm mt-1">
              All your images, videos, and audio files from your workspaces
            </p>
          </div>
        </div>
        
        {/* Media Feed Gallery */}
        <div className="min-h-96">
          <WorkspaceMediaGallery 
            onMediaSelect={(media) => {
              setSelectedMedia(media);
            }}
            selectedMedia={selectedMedia}
            className="h-full"
          />
        </div>
      </div>



      {/* Media Gallery Modal */}
      {showMediaGallery && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
          <div className="bg-[#0a0a0a] rounded-lg w-full max-w-7xl h-[90vh] overflow-hidden relative">
            {/* Close Button */}
            <button
              onClick={() => setShowMediaGallery(false)}
              className="absolute top-4 right-4 z-10 p-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
            >
              <X className="w-5 h-5 text-white" />
            </button>
            
            {/* Media Gallery */}
            <WorkspaceMediaGallery 
              onMediaSelect={(media) => {
                setSelectedMedia(media);
                // You can add additional actions here when media is selected
              }}
              selectedMedia={selectedMedia}
              className="h-full overflow-hidden"
            />
          </div>
        </div>
      )}
    </div>
  );
}
