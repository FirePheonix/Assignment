"use client";

import Image from "next/image";
import Link from "next/link";
import { useRef, useState, useEffect } from "react";
import { publicWorkspaceApi } from "@/lib/workspace-api";
import type { Workspace, WorkspaceMedia } from "@/lib/workspace-api";
import { Eye, Download, User, Clock, Play, ExternalLink, X } from "lucide-react";
import { Dialog, DialogContent } from "@/components/flow-components/ui/dialog";
import { Button } from "@/components/flow-components/ui/button";
import { UserAvatar } from "@/components/user-avatar";

export default function FeedPage() {
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<'recent' | 'popular' | 'most_cloned'>('recent');
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [selectedItem, setSelectedItem] = useState<(WorkspaceMedia & { workspace: Workspace }) | null>(null);

  // Flatten all media from all workspaces
  const feedItems: Array<WorkspaceMedia & { workspace: Workspace }> = workspaces.flatMap(workspace =>
    workspace.media.map(media => ({ ...media, workspace }))
  );

  useEffect(() => {
    loadFeed();
  }, [sortBy, searchQuery]);

  const loadFeed = async () => {
    try {
      setIsLoading(true);
      const data = await publicWorkspaceApi.list(sortBy, searchQuery || undefined);
      setWorkspaces(data);
    } catch (error) {
      console.error('Error loading feed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Top Bar */}
      <div className="fixed top-3 z-50 bg-[#1a1a1a]/80 backdrop-blur-xl px-8 py-3 mb-6 rounded-2xl overlay-blur">
        <div className="flex items-center justify-between max-w-[2000px] mx-auto">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <svg 
              className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search workflows..."
              className="w-full bg-transparent border-none pl-10 pr-4 py-2 text-sm text-white/50 placeholder:text-white/40 focus:outline-none focus:text-white transition-colors"
            />
          </div>
          
          {/* Sort Menu */}
          <div className="relative">
            <button 
              onClick={() => setShowSortMenu(!showSortMenu)}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/10"
            >
              <Clock className="w-4 h-4 text-white/60" />
              <span className="text-sm text-white/60 capitalize">{sortBy === 'most_cloned' ? 'Most Imported' : sortBy}</span>
            </button>

            {/* Sort Dropdown */}
            {showSortMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl p-2">
                {[
                  { value: 'recent' as const, label: 'Recent' },
                  { value: 'popular' as const, label: 'Popular' },
                  { value: 'most_cloned' as const, label: 'Most Imported' },
                ].map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setSortBy(option.value);
                      setShowSortMenu(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                      sortBy === option.value
                        ? 'bg-purple-500 text-white'
                        : 'text-white/60 hover:bg-white/10'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Masonry Grid */}
      <div className="px-4 pb-8 max-w-[2000px] mx-auto py-18 rounded-2xl">
        {isLoading ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <p className="text-white/40">Loading feed...</p>
          </div>
        ) : feedItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <p className="text-white/40 text-lg mb-2">No published workflows yet</p>
            <p className="text-white/30 text-sm">Be the first to publish your AI workflow!</p>
          </div>
        ) : (
          <div className="columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-0.5">
            {feedItems.map((item, index) => (
              <div
                key={`${item.workspace.id}-${item.id}`}
                onClick={() => setSelectedItem(item)}
                className="block break-inside-avoid mb-0.5 relative group cursor-pointer overflow-hidden"
              >
                {item.mediaType === "image" ? (
                  <div className="relative w-full">
                    <Image
                      src={item.fileUrl}
                      alt={item.title || item.workspace.name}
                      width={400}
                      height={600}
                      className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                      unoptimized
                    />
                  </div>
                ) : (
                  <div className="relative">
                    <video
                      ref={(el) => {
                        videoRefs.current[index] = el;
                      }}
                      src={item.fileUrl}
                      poster={item.thumbnailUrl}
                      loop
                      muted
                      playsInline
                      className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                      onMouseEnter={(e) => e.currentTarget.play()}
                      onMouseLeave={(e) => {
                        e.currentTarget.pause();
                        e.currentTarget.currentTime = 0;
                      }}
                    />
                    <div className="absolute top-2 right-2 p-1.5 bg-black/60 backdrop-blur-sm rounded-full">
                      <Play className="w-3 h-3 text-white" />
                    </div>
                  </div>
                )}
                
                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    {/* Workflow Name */}
                    <h3 className="text-white font-medium text-sm mb-2 line-clamp-1">
                      {item.workspace.name}
                    </h3>
                    
                    {/* Description */}
                    {item.workspace.description && (
                      <p className="text-white/70 text-xs mb-3 line-clamp-2">
                        {item.workspace.description}
                      </p>
                    )}
                    
                    {/* Stats */}
                    <div className="flex items-center gap-3 text-white/60 text-xs">
                      <Link 
                        href={`/users/${item.workspace.userId}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1.5 hover:text-purple-400 transition-colors"
                      >
                        <UserAvatar 
                          user={{ 
                            profile_picture: item.workspace.userProfilePicture,
                            username: item.workspace.userName 
                          }} 
                          size="sm" 
                        />
                        <span>{item.workspace.userName}</span>
                      </Link>
                      <div className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        <span>{item.workspace.viewCount}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="w-3 h-3" />
                        <span>{item.workspace.cloneCount}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Workspace Preview Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="max-w-2xl bg-[#1a1a1a] border-white/10">
          {selectedItem && (
            <div className="space-y-4">
              {/* Media Preview */}
              <div className="relative rounded-lg overflow-hidden">
                {selectedItem.mediaType === "image" ? (
                  <Image
                    src={selectedItem.fileUrl}
                    alt={selectedItem.title || selectedItem.workspace.name}
                    width={800}
                    height={600}
                    className="w-full h-auto"
                    unoptimized
                  />
                ) : (
                  <video
                    src={selectedItem.fileUrl}
                    poster={selectedItem.thumbnailUrl}
                    controls
                    className="w-full h-auto"
                  />
                )}
              </div>

              {/* Workflow Info */}
              <div className="space-y-3">
                <h2 className="text-2xl font-bold text-white">
                  {selectedItem.workspace.name}
                </h2>
                
                {selectedItem.workspace.description && (
                  <p className="text-white/70">
                    {selectedItem.workspace.description}
                  </p>
                )}

                {/* Creator & Stats */}
                <div className="flex items-center gap-4 text-sm text-white/60">
                  <Link 
                    href={`/users/${selectedItem.workspace.userId}`}
                    className="flex items-center gap-2 hover:text-purple-400 transition-colors"
                  >
                    <UserAvatar 
                      user={{ 
                        profile_picture: selectedItem.workspace.userProfilePicture,
                        username: selectedItem.workspace.userName 
                      }} 
                      size="sm" 
                    />
                    <span>By {selectedItem.workspace.userName}</span>
                  </Link>
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>{selectedItem.workspace.viewCount} views</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    <span>{selectedItem.workspace.cloneCount} imports</span>
                  </div>
                </div>

                {/* Open Workflow Button */}
                <Link href={`/flow-generator/${selectedItem.workspace.slug}`}>
                  <Button className="w-full gap-2 bg-purple-600 hover:bg-purple-700">
                    <ExternalLink className="w-4 h-4" />
                    Open Workflow
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
