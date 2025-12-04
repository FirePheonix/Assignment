"use client";

import { Calendar, Clock, Plus, Play, Edit, Trash2, AlertCircle, ExternalLink, CheckCircle, Instagram } from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { useInstagramPosts } from "@/hooks/use-instagram";
import { useBrands } from "@/hooks/use-brands";
import { ImageGallery, ImageUploadBox } from "@/components/ImageGallery";
import Link from "next/link";
import { CreatePostData } from "@/lib/api/instagram";
import type { Brand } from "@/lib/api/brands";
import { toast } from "sonner";

interface Post {
  id: number;
  image?: string | null;
  content?: string | null;
  caption?: string | null;
  scheduled_for?: string | null;
  scheduled_time?: string | null;
  scheduled_at?: string | null;
  posted_at?: string | null;
  created_at?: string | null;
  status?: string;
  instagram_url?: string | null;
  brand: {
    id: number;
    name: string;
  };
  // extend as needed
}

interface CreatePostFormData {
  caption: string;
  image: string;
  scheduled_time: string;
  brand_id: number;
}

export default function InstagramQueuePage() {
  const { brands = [], isLoading: brandsLoading } = useBrands();

  // Fetch posts from ALL brands (pass undefined to get all)
  const {
    posts = [],
    isLoading = false,
    createPost,
    updatePost,
    deletePost,
    postNow,
    refetch,
  } = useInstagramPosts(undefined);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showImageGallery, setShowImageGallery] = useState(false);
  const [editingPost, setEditingPost] = useState<Post | null>(null);

  const [formData, setFormData] = useState<CreatePostFormData>({
    caption: '',
    image: '',
    scheduled_time: '',
    brand_id: 0, // no auto-select — user must choose
  });

  // derived lists
  const connectedBrands = (brands || []).filter((b: Brand) => !!b.instagram_connected);

  const queueStats = useMemo(() => {
    const approved = posts.filter(p => p.status === 'approved').length;
    const posted = posts.filter(p => p.status === 'posted').length;
    const drafts = posts.filter(p => p.status === 'draft').length;

    return {
      total: posts.length,
      approved,
      posted,
      drafts,
    };
  }, [posts]);

  // Utility: convert backend date string to value acceptable by <input type="datetime-local" />
  // Expects an ISO-ish string; fallback returns ''
  const toDateTimeLocal = (dateStr?: string | null) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    // produce "YYYY-MM-DDTHH:MM"
    const pad = (n: number) => String(n).padStart(2, '0');
    const YYYY = d.getFullYear();
    const MM = pad(d.getMonth() + 1);
    const DD = pad(d.getDate());
    const HH = pad(d.getHours());
    const mm = pad(d.getMinutes());
    return `${YYYY}-${MM}-${DD}T${HH}:${mm}`;
  };

  useEffect(() => {
    // If brands just loaded and user opened form while editing is null, keep brand_id = 0 (manual choice)
    // Do nothing else here — we do not auto-select any brand.
  }, [brandsLoading]);

  const handleCreatePost = async () => {
    if (!formData.caption.trim()) {
      toast.error('Please enter a caption');
      return;
    }

    if (!formData.image) {
      toast.error('Please select an image');
      return;
    }

    if (!formData.brand_id) {
      toast.error('Please select a brand');
      return;
    }

    try {
      const postData: CreatePostData = {
        caption: formData.caption,
        imageUrl: formData.image,
        brand_id: formData.brand_id,
      };

      if (formData.scheduled_time) {
        postData.scheduled_time = formData.scheduled_time;
      }

      await createPost(postData);
      toast.success('Post created successfully!');

      // Reset form to manual-brand mode (brand_id = 0)
      setFormData({
        caption: '',
        image: '',
        scheduled_time: '',
        brand_id: 0,
      });
      setShowCreateForm(false);
      setShowImageGallery(false);
      refetch?.();
    } catch (error) {
      console.error('Failed to create post:', error);
      toast.error('Failed to create post');
    }
  };

  const handleUpdatePost = async () => {
    if (!editingPost) return;
    if (!formData.caption.trim()) {
      toast.error('Please enter a caption');
      return;
    }
    if (!formData.brand_id) {
      toast.error('Please select a brand');
      return;
    }

    try {
      const updateData: Partial<CreatePostData> = {
        caption: formData.caption,
        brand_id: formData.brand_id,
      };

      if (formData.image && formData.image !== (editingPost.image ?? '')) {
        updateData.imageUrl = formData.image;
      }

      // Compare scheduled times normalized
      const existingScheduled = toDateTimeLocal(editingPost.scheduled_for ?? editingPost.scheduled_time ?? undefined);
      if (formData.scheduled_time !== existingScheduled) {
        updateData.scheduled_time = formData.scheduled_time || undefined;
      }

      await updatePost(editingPost.id, updateData);
      toast.success('Post updated successfully!');

      // cleanup
      setEditingPost(null);
      setFormData({
        caption: '',
        image: '',
        scheduled_time: '',
        brand_id: 0,
      });
      setShowCreateForm(false);
      setShowImageGallery(false);
      refetch?.();
    } catch (error) {
      console.error('Failed to update post:', error);
      toast.error('Failed to update post');
    }
  };

  const handleEditPost = (post: Post) => {
    setEditingPost(post);
    setFormData({
      caption: post.content ?? post.caption ?? '',
      image: post.image ?? '',
      scheduled_time: toDateTimeLocal(post.scheduled_for ?? post.scheduled_time ?? undefined),
      brand_id: post.brand?.id ?? 0,
    });
    setShowCreateForm(true);
    setShowImageGallery(false);
  };

  const handleCancelEdit = () => {
    setEditingPost(null);
    setFormData({
      caption: '',
      image: '',
      scheduled_time: '',
      brand_id: 0,
    });
    setShowCreateForm(false);
    setShowImageGallery(false);
  };

  const handlePostNow = async (postId: number) => {
    if (confirm('Are you sure you want to post this to Instagram now?')) {
      try {
        await postNow(postId);
        refetch?.();
      } catch (err) {
        console.error('Post now failed:', err);
        alert('Failed to post now');
      }
    }
  };

  const handleDeletePost = async (postId: number) => {
    if (confirm('Are you sure you want to delete this post?')) {
      try {
        await deletePost(postId);
        refetch?.();
      } catch (err) {
        console.error('Delete failed:', err);
        alert('Failed to delete post');
      }
    }
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '';
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString();
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'posted': return 'text-green-400 bg-green-500/20';
      case 'approved': return 'text-blue-400 bg-blue-500/20';
      case 'scheduled': return 'text-blue-400 bg-blue-500/20';
      case 'draft': return 'text-gray-400 bg-gray-500/20';
      case 'failed': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <nav className="text-sm text-gray-400 mb-2">
          <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
          <span className="mx-2">→</span>
          <Link href="/dashboard/brands" className="hover:text-white transition-colors">Brands</Link>
          <span className="mx-2">→</span>
          <span className="text-purple-400">Instagram Queue</span>
        </nav>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Instagram Post Queue</h1>
            <p className="text-gray-400">All scheduled Instagram posts across all your brands</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/instagram/connect"
              className="bg-white/5 border border-white/10 hover:bg-white/10 text-white py-2 px-4 rounded-lg transition-colors"
            >
              Connections
            </Link>
            <button
              onClick={() => setShowCreateForm(true)}
              disabled={connectedBrands.length === 0}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg transition-opacity"
            >
              Create Post
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-400">{queueStats.total}</div>
                <div className="text-sm text-gray-500">Total Posts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">{queueStats.posted}</div>
                <div className="text-sm text-gray-500">Posted</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">{queueStats.approved}</div>
                <div className="text-sm text-gray-500">Approved</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-500">{queueStats.drafts}</div>
                <div className="text-sm text-gray-500">Drafts</div>
              </div>
            </div>
          </div>

          {/* Create Post Button */}
          {!showCreateForm && (
            <div className="mb-6">
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create New Post
              </button>
            </div>
          )}

          {/* Create/Edit Post Form */}
          {showCreateForm && (
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  {editingPost ? 'Edit Post' : 'Create New Post'}
                </h3>
                <button
                  onClick={handleCancelEdit}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Caption</label>
                  <textarea
                    rows={4}
                    maxLength={2200}
                    value={formData.caption}
                    onChange={(e) => setFormData(prev => ({ ...prev, caption: e.target.value }))}
                    className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="Write your caption..."
                  />
                  <div className="text-xs text-gray-500 mt-1">{formData.caption.length} / 2200 characters</div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Media</label>
                    <div className="space-y-3">
                      {formData.image ? (
                        <div className="relative aspect-square">
                          {formData.image.match(/\.(mp4|mov|avi|webm)$/i) ? (
                            <video
                              src={formData.image}
                              controls
                              className="w-full h-full object-cover rounded-lg border border-white/10"
                            />
                          ) : (
                            <img
                              src={formData.image}
                              alt="Preview"
                              className="w-full h-full object-cover rounded-lg border border-white/10"
                            />
                          )}
                          <button
                            onClick={() => setFormData(prev => ({ ...prev, image: '' }))}
                            className="absolute top-2 right-2 p-1.5 bg-red-500 rounded-full text-white hover:bg-red-600 transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <ImageUploadBox
                          currentImage={formData.image}
                          onImageUpload={(url: string) => setFormData(prev => ({ ...prev, image: url }))}
                          className="aspect-square"
                        />
                      )}
                      <button
                        onClick={() => setShowImageGallery(!showImageGallery)}
                        className="w-full text-purple-400 hover:text-purple-300 text-sm py-2 border border-purple-400/30 rounded-lg hover:bg-purple-500/10 transition"
                        type="button"
                      >
                        {showImageGallery ? 'Hide' : 'Show'} Image Library
                      </button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">Brand</label>
                      <select
                        value={formData.brand_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, brand_id: Number(e.target.value) }))}
                        className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={!!editingPost}
                      >
                        <option value={0} disabled>
                          -- Select Brand --
                        </option>
                        {brands.map((b: Brand) => (
                          <option key={b.id} value={b.id}>
                            {b.name} {b.has_instagram_config ? '✓' : '(not connected)'}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        {editingPost ? 'Brand cannot be changed when editing' : 'Select a brand to create a post'}
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">Schedule For (Optional)</label>
                      <input
                        type="datetime-local"
                        value={formData.scheduled_time}
                        onChange={(e) => setFormData(prev => ({ ...prev, scheduled_time: e.target.value }))}
                        min={new Date().toISOString().slice(0, 16)}
                        className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Leave empty to save as draft
                      </p>
                    </div>
                  </div>
                </div>

                {showImageGallery && (
                  <ImageGallery
                    selectedImage={formData.image}
                    onImageSelect={(imageUrl: string) => {
                      setFormData(prev => ({ ...prev, image: imageUrl }));
                      setShowImageGallery(false);
                    }}
                    showUpload={false}
                  />
                )}

                <div className="flex gap-3">
                  <button
                    onClick={editingPost ? handleUpdatePost : handleCreatePost}
                    disabled={!formData.caption.trim() || !formData.image || !formData.brand_id}
                    className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2"
                  >
                    {editingPost ? <Edit className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                    {editingPost ? 'Update Post' : 'Create Post'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Timeline View */}
          <div className="space-y-6">
            {isLoading ? (
              <div className="text-center py-12 bg-[#1a1a1a] border border-white/10 rounded-xl">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p className="text-gray-400">Loading posts...</p>
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-12 bg-[#1a1a1a] border border-white/10 rounded-xl">
                <Instagram className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-400 mb-2">No posts yet</h4>
                <p className="text-sm text-gray-500 mb-6">
                  Create your first Instagram post to get started
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Post
                </button>
              </div>
            ) : (
              (() => {
                // Group posts by date categories
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
                const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

                const grouped: Record<string, Post[]> = {
                  overdue: [],
                  today: [],
                  tomorrow: [],
                  thisWeek: [],
                  later: [],
                  posted: [],
                  drafts: [],
                };

                posts.forEach((post) => {
                  if (post.status === 'posted') {
                    grouped.posted.push(post);
                  } else if (!post.scheduled_for && !post.scheduled_time) {
                    grouped.drafts.push(post);
                  } else {
                    const scheduledDate = new Date(post.scheduled_for || post.scheduled_time || '');
                    if (isNaN(scheduledDate.getTime())) {
                      grouped.drafts.push(post);
                    } else if (scheduledDate < now) {
                      grouped.overdue.push(post);
                    } else if (scheduledDate < tomorrow) {
                      grouped.today.push(post);
                    } else if (scheduledDate < new Date(tomorrow.getTime() + 24 * 60 * 60 * 1000)) {
                      grouped.tomorrow.push(post);
                    } else if (scheduledDate < nextWeek) {
                      grouped.thisWeek.push(post);
                    } else {
                      grouped.later.push(post);
                    }
                  }
                });

                const sections = [
                  { key: 'overdue', title: 'Overdue', color: 'text-red-400', icon: AlertCircle },
                  { key: 'today', title: 'Today', color: 'text-green-400', icon: Clock },
                  { key: 'tomorrow', title: 'Tomorrow', color: 'text-blue-400', icon: Calendar },
                  { key: 'thisWeek', title: 'This Week', color: 'text-purple-400', icon: Calendar },
                  { key: 'later', title: 'Later', color: 'text-gray-400', icon: Calendar },
                  { key: 'posted', title: 'Posted', color: 'text-green-400', icon: CheckCircle },
                  { key: 'drafts', title: 'Drafts', color: 'text-gray-400', icon: Edit },
                ];

                return (
                  <>
                    {sections.map(section => {
                      const sectionPosts = grouped[section.key];
                      if (sectionPosts.length === 0) return null;

                      const Icon = section.icon;

                      return (
                        <div key={section.key} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
                          <div className="flex items-center gap-3 mb-4">
                            <Icon className={`w-5 h-5 ${section.color}`} />
                            <h3 className={`text-lg font-semibold ${section.color}`}>
                              {section.title}
                            </h3>
                            <span className="text-sm text-gray-500">({sectionPosts.length})</span>
                          </div>

                          <div className="space-y-3">
                            {sectionPosts.map((post) => (
                              <div
                                key={post.id}
                                className="bg-black border border-white/10 rounded-lg p-4 hover:border-purple-500/50 transition"
                              >
                                <div className="flex gap-4">
                                  {/* Thumbnail */}
                                  <div className="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-gray-900">
                                    {post.image ? (
                                      post.image.match(/\.(mp4|mov|avi|webm)$/i) ? (
                                        <video
                                          src={post.image}
                                          className="w-full h-full object-cover"
                                          muted
                                          playsInline
                                        />
                                      ) : (
                                        <img
                                          src={post.image}
                                          alt="Post"
                                          className="w-full h-full object-cover"
                                        />
                                      )
                                    ) : (
                                      <div className="w-full h-full flex items-center justify-center">
                                        <Instagram className="w-8 h-8 text-gray-600" />
                                      </div>
                                    )}
                                  </div>

                                  {/* Content */}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-4 mb-2">
                                      <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold">
                                          {post.brand?.name?.substring(0, 1).toUpperCase() ?? '?'}
                                        </div>
                                        <span className="text-sm font-medium text-white">{post.brand?.name ?? 'Unknown'}</span>
                                        <span className={`text-xs px-2 py-1 rounded ${getStatusColor(post.status)}`}>
                                          {post.status || 'unknown'}
                                        </span>
                                      </div>

                                      {post.instagram_url && (
                                        <a
                                          href={post.instagram_url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-purple-400 hover:text-purple-300 flex items-center gap-1 text-xs"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          View
                                        </a>
                                      )}
                                    </div>

                                    <p className="text-gray-300 text-sm mb-2 line-clamp-2">
                                      {post.content || post.caption || 'No caption'}
                                    </p>

                                    <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
                                      {(post.scheduled_for || post.scheduled_time) && (
                                        <div className="flex items-center gap-1">
                                          <Clock className="w-3 h-3" />
                                          {formatDate(post.scheduled_for || post.scheduled_time)}
                                        </div>
                                      )}
                                      {post.posted_at && (
                                        <div className="flex items-center gap-1">
                                          <CheckCircle className="w-3 h-3" />
                                          Posted {formatDate(post.posted_at)}
                                        </div>
                                      )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                      {post.status !== 'posted' && (
                                        <>
                                          <button
                                            onClick={() => handlePostNow(post.id)}
                                            className="text-green-400 hover:text-green-300 text-xs px-3 py-1.5 rounded bg-green-500/10 hover:bg-green-500/20 transition flex items-center gap-1"
                                          >
                                            <Play className="w-3 h-3" />
                                            Post Now
                                          </button>
                                          <button
                                            onClick={() => handleEditPost(post)}
                                            className="text-blue-400 hover:text-blue-300 text-xs px-3 py-1.5 rounded bg-blue-500/10 hover:bg-blue-500/20 transition flex items-center gap-1"
                                          >
                                            <Edit className="w-3 h-3" />
                                            Edit
                                          </button>
                                        </>
                                      )}
                                      <button
                                        onClick={() => handleDeletePost(post.id)}
                                        className="text-red-400 hover:text-red-300 text-xs px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 transition flex items-center gap-1"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                        Delete
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </>
                );
              })()
            )}
          </div>
    </div>
  );
}
