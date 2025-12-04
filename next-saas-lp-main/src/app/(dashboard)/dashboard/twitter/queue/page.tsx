"use client";

import { Calendar, Clock, Plus, Play, Edit, Trash2, AlertCircle, CheckCircle, ExternalLink, Twitter, Upload, X, Sparkles, Video, Image as ImageIcon } from "lucide-react";
import { useState, useMemo } from "react";
import { useTwitterQueue } from "@/hooks/use-twitter";
import { useBrands } from "@/hooks/use-brands";
import Link from "next/link";
import { CreateTweetData, twitterAPI } from "@/lib/api/twitter";
import type { Brand } from "@/lib/api/brands";
import { toast } from "sonner";

interface Tweet {
  id: number;
  content: string;
  status: 'draft' | 'queued' | 'scheduled' | 'posted' | 'failed';
  scheduled_at: string | null;
  posted_at: string | null;
  media_urls: string[];
  twitter_id: string | null;
  twitter_url: string | null;
  error_message: string | null;
  brand: {
    id: number;
    name: string;
    slug: string;
  };
  created_at: string;
  updated_at: string;
}

interface CreateTweetFormData {
  content: string;
  scheduled_at: string;
  brand_id: number;
  media_urls: string[];
}

export default function TwitterQueuePage() {
  const { brands = [], isLoading: brandsLoading } = useBrands();

  // Fetch tweets from ALL brands (pass undefined to get all)
  const {
    tweets = [],
    isLoading = false,
    stats = { total_queued: 0, total_scheduled: 0, total_drafts: 0, total_posted: 0 },
    createTweet,
    updateTweet,
    deleteTweet,
    postNow,
    generateAITweets,
    refetch,
  } = useTwitterQueue(undefined);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTweet, setEditingTweet] = useState<Tweet | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadingMedia, setUploadingMedia] = useState(false);
  const [showAIPrompt, setShowAIPrompt] = useState(false);
  const [aiPrompt, setAIPrompt] = useState('');

  const [formData, setFormData] = useState<CreateTweetFormData>({
    content: '',
    scheduled_at: '',
    brand_id: 0,
    media_urls: [],
  });

  // derived lists
  const connectedBrands = (brands || []).filter((b: Brand) => {
    // Check if brand has twitter credentials
    return b.has_twitter_config;
  });

  // Utility: convert backend date string to value acceptable by <input type="datetime-local" />
  const toDateTimeLocal = (dateStr?: string | null) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const pad = (n: number) => String(n).padStart(2, '0');
    const YYYY = d.getFullYear();
    const MM = pad(d.getMonth() + 1);
    const DD = pad(d.getDate());
    const HH = pad(d.getHours());
    const mm = pad(d.getMinutes());
    return `${YYYY}-${MM}-${DD}T${HH}:${mm}`;
  };

  const handleCreateTweet = async () => {
    if (!formData.content.trim()) {
      toast.error('Please enter tweet content');
      return;
    }

    if (formData.content.length > 280) {
      toast.error('Tweet must be 280 characters or less');
      return;
    }

    if (!formData.brand_id) {
      toast.error('Please select a brand');
      return;
    }

    try {
      const tweetData: CreateTweetData & { brand_id: number } = {
        content: formData.content,
        brand_id: formData.brand_id,
        media_urls: formData.media_urls.length > 0 ? formData.media_urls : undefined,
      };

      if (formData.scheduled_at) {
        tweetData.scheduled_at = formData.scheduled_at;
      }

      await createTweet(tweetData);

      // Reset form
      setFormData({
        content: '',
        scheduled_at: '',
        brand_id: 0,
        media_urls: [],
      });
      setShowCreateForm(false);
      setShowAIPrompt(false);
      setAIPrompt('');
      refetch?.();
    } catch (error) {
      console.error('Failed to create tweet:', error);
    }
  };

  const handleUpdateTweet = async () => {
    if (!editingTweet) return;
    if (!formData.content.trim()) {
      toast.error('Please enter tweet content');
      return;
    }
    if (formData.content.length > 280) {
      toast.error('Tweet must be 280 characters or less');
      return;
    }

    try {
      const updateData: Partial<CreateTweetData> = {
        content: formData.content,
        media_urls: formData.media_urls,
      };

      // Compare scheduled times normalized
      const existingScheduled = toDateTimeLocal(editingTweet.scheduled_at);
      if (formData.scheduled_at !== existingScheduled) {
        updateData.scheduled_at = formData.scheduled_at || null;
      }

      await updateTweet(editingTweet.id, updateData);

      // cleanup
      setEditingTweet(null);
      setFormData({
        content: '',
        scheduled_at: '',
        brand_id: 0,
        media_urls: [],
      });
      setShowCreateForm(false);
      setShowAIPrompt(false);
      setAIPrompt('');
      refetch?.();
    } catch (error) {
      console.error('Failed to update tweet:', error);
    }
  };

  const handleEditTweet = (tweet: Tweet) => {
    setEditingTweet(tweet);
    setFormData({
      content: tweet.content,
      scheduled_at: toDateTimeLocal(tweet.scheduled_at),
      brand_id: tweet.brand?.id ?? 0,
      media_urls: tweet.media_urls || [],
    });
    setShowCreateForm(true);
  };

  const handleCancelEdit = () => {
    setEditingTweet(null);
    setFormData({
      content: '',
      scheduled_at: '',
      brand_id: 0,
      media_urls: [],
    });
    setShowCreateForm(false);
    setShowAIPrompt(false);
    setAIPrompt('');
  };

  const handlePostNow = async (tweetId: number) => {
    if (confirm('Are you sure you want to post this tweet now?')) {
      try {
        await postNow(tweetId);
        refetch?.();
      } catch (err) {
        console.error('Post now failed:', err);
      }
    }
  };

  const handleMediaUpload = async (file: File) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      toast.error('Please select an image or video file');
      return;
    }

    // Validate file size (100MB limit for videos, 10MB for images)
    const maxSize = file.type.startsWith('video/') ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${file.type.startsWith('video/') ? '100MB' : '10MB'}`);
      return;
    }

    setUploadingMedia(true);
    try {
      const result = await twitterAPI.uploadMedia(file);
      if (result.success && result.url) {
        setFormData(prev => ({
          ...prev,
          media_urls: [...prev.media_urls, result.url!]
        }));
        toast.success('Media uploaded successfully!');
      } else {
        toast.error(result.error || 'Failed to upload media');
      }
    } catch (error) {
      console.error('Media upload failed:', error);
      toast.error('Failed to upload media');
    } finally {
      setUploadingMedia(false);
    }
  };

  const handleRemoveMedia = (index: number) => {
    setFormData(prev => ({
      ...prev,
      media_urls: prev.media_urls.filter((_, i) => i !== index)
    }));
  };

  const handleGenerateAIText = async () => {
    if (!aiPrompt.trim()) {
      toast.error('Please enter a prompt for AI generation');
      return;
    }

    if (!formData.brand_id) {
      toast.error('Please select a brand first');
      return;
    }

    setIsGenerating(true);
    try {
      // Use the hook's generateAITweets function
      const result = await generateAITweets(formData.brand_id, {
        prompt: aiPrompt,
        count: 1,
        tone: 'professional',
      });

      if (result.success && result.tweets && result.tweets.length > 0) {
        // Use the generated tweet content and delete the created draft
        const generatedContent = result.tweets[0].content;
        setFormData(prev => ({ ...prev, content: generatedContent }));
        
        // Delete the draft tweet that was created
        try {
          await deleteTweet(result.tweets[0].id);
        } catch (err) {
          console.error('Failed to delete draft:', err);
        }
        
        setShowAIPrompt(false);
        setAIPrompt('');
        toast.success('AI text generated!');
        
        // Queue is already refreshed by the hook's generateAITweets
      } else {
        toast.error(result.error || 'Failed to generate text');
      }
    } catch (error: any) {
      console.error('AI generation failed:', error);
      toast.error(error.message || 'Failed to generate AI text');
    } finally {
      setIsGenerating(false);
    }
  };

  const isVideo = (url: string) => {
    return url.match(/\.(mp4|mov|avi|webm)$/i);
  };

  const handleDeleteTweet = async (tweetId: number) => {
    if (confirm('Are you sure you want to delete this tweet?')) {
      try {
        await deleteTweet(tweetId);
        refetch?.();
      } catch (err) {
        console.error('Delete failed:', err);
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
      case 'scheduled': return 'text-blue-400 bg-blue-500/20';
      case 'queued': return 'text-purple-400 bg-purple-500/20';
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
          <span className="text-blue-400">Twitter Queue</span>
        </nav>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Twitter/X Post Queue</h1>
            <p className="text-gray-400">All scheduled tweets across all your brands</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/twitter/config"
              className="bg-white/5 border border-white/10 hover:bg-white/10 text-white py-2 px-4 rounded-lg transition-colors"
            >
              Configuration
            </Link>
            <button
              onClick={() => setShowCreateForm(true)}
              disabled={connectedBrands.length === 0}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg transition-opacity"
            >
              Create Tweet
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-400">{stats.total_posted + stats.total_scheduled + stats.total_drafts}</div>
            <div className="text-sm text-gray-500">Total Tweets</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-500">{stats.total_posted}</div>
            <div className="text-sm text-gray-500">Posted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-500">{stats.total_scheduled}</div>
            <div className="text-sm text-gray-500">Scheduled</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-500">{stats.total_drafts}</div>
            <div className="text-sm text-gray-500">Drafts</div>
          </div>
        </div>
      </div>

      {/* Create Post Button */}
      {!showCreateForm && (
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => setShowCreateForm(true)}
            disabled={connectedBrands.length === 0}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 disabled:opacity-50 text-white font-medium py-3 px-6 rounded-lg transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create New Tweet
          </button>
          {connectedBrands.length === 0 && (
            <p className="text-sm text-gray-400 mt-2">
              No brands with Twitter configured. <Link href="/dashboard/twitter/config" className="text-blue-400 hover:text-blue-300">Configure Twitter</Link>
            </p>
          )}
        </div>
      )}

      {/* Create/Edit Tweet Form */}
      {showCreateForm && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              {editingTweet ? 'Edit Tweet' : 'Create New Tweet'}
            </h3>
            <button
              onClick={handleCancelEdit}
              className="text-gray-400 hover:text-white z-10 relative"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            {/* Tweet Content with AI Button */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-400">Tweet Content</label>
                <button
                  type="button"
                  onClick={() => setShowAIPrompt(!showAIPrompt)}
                  disabled={!formData.brand_id}
                  className="text-purple-400 hover:text-purple-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-1 relative z-10"
                >
                  <Sparkles className="w-4 h-4" />
                  {showAIPrompt ? 'Hide' : 'Generate with AI'}
                </button>
              </div>

              {/* AI Prompt Input */}
              {showAIPrompt && (
                <div className="mb-3 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAIPrompt(e.target.value)}
                    placeholder="Describe what the tweet should be about..."
                    className="w-full p-2 bg-black border border-purple-500/30 rounded text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 mb-2"
                  />
                  <button
                    onClick={handleGenerateAIText}
                    disabled={!aiPrompt.trim() || isGenerating}
                    className="bg-gradient-to-r from-purple-500 to-pink-600 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm font-medium transition flex items-center gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3" />
                        Generate Text
                      </>
                    )}
                  </button>
                </div>
              )}

              <textarea
                rows={4}
                maxLength={280}
                value={formData.content}
                onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="What's happening?"
              />
              <div className="text-xs text-gray-500 mt-1">{formData.content.length} / 280 characters</div>
            </div>

            {/* Media Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Media (Optional)</label>
              <div className="space-y-3">
                {/* Media Preview Grid */}
                {formData.media_urls.length > 0 && (
                  <div className="grid grid-cols-2 gap-3">
                    {formData.media_urls.map((url, index) => (
                      <div key={index} className="relative aspect-video rounded-lg overflow-hidden border border-white/10">
                        {isVideo(url) ? (
                          <video
                            src={url}
                            controls
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <img
                            src={url}
                            alt={`Media ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        )}
                        <button
                          onClick={() => handleRemoveMedia(index)}
                          className="absolute top-2 right-2 p-1.5 bg-red-500 rounded-full text-white hover:bg-red-600 transition"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        {isVideo(url) && (
                          <div className="absolute top-2 left-2 bg-black/70 p-1.5 rounded">
                            <Video className="w-3 h-3 text-white" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Upload Button */}
                {formData.media_urls.length < 4 && (
                  <label className="bg-white/5 border border-white/10 hover:bg-white/10 text-gray-400 hover:text-white px-4 py-2 rounded-lg font-medium transition inline-flex items-center gap-2 cursor-pointer">
                    {uploadingMedia ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Uploading...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        <span>Upload Media</span>
                      </>
                    )}
                    <input
                      type="file"
                      accept="image/*,video/*"
                      onChange={(e) => e.target.files && handleMediaUpload(e.target.files[0])}
                      className="hidden"
                      disabled={uploadingMedia}
                    />
                  </label>
                )}
                <p className="text-xs text-gray-500">
                  Images (JPG, PNG up to 10MB) or Videos (MP4 up to 100MB). Max 4 files.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Brand</label>
                <select
                  value={formData.brand_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, brand_id: Number(e.target.value) }))}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={!!editingTweet}
                >
                  <option value={0} disabled>
                    -- Select Brand --
                  </option>
                  {brands.map((b: Brand) => (
                    <option key={b.id} value={b.id}>
                      {b.name} {b.has_twitter_config ? '✓' : '(not connected)'}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {editingTweet ? 'Brand cannot be changed when editing' : 'Select a brand to post from'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Schedule For (Optional)</label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_at}
                  onChange={(e) => setFormData(prev => ({ ...prev, scheduled_at: e.target.value }))}
                  min={new Date().toISOString().slice(0, 16)}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to save as draft
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={editingTweet ? handleUpdateTweet : handleCreateTweet}
                disabled={!formData.content.trim() || !formData.brand_id}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2"
              >
                {editingTweet ? <Edit className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                {editingTweet ? 'Update Tweet' : 'Create Tweet'}
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
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading tweets...</p>
          </div>
        ) : tweets.length === 0 ? (
          <div className="text-center py-12 bg-[#1a1a1a] border border-white/10 rounded-xl">
            <Twitter className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-400 mb-2">No tweets yet</h4>
            <p className="text-sm text-gray-500 mb-6">
              Create your first tweet to get started
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              disabled={connectedBrands.length === 0}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Tweet
            </button>
          </div>
        ) : (
          (() => {
            // Group tweets by date categories
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
            const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

            const grouped: Record<string, Tweet[]> = {
              overdue: [],
              today: [],
              tomorrow: [],
              thisWeek: [],
              later: [],
              posted: [],
              drafts: [],
            };

            tweets.forEach((tweet) => {
              if (tweet.status === 'posted') {
                grouped.posted.push(tweet);
              } else if (!tweet.scheduled_at) {
                grouped.drafts.push(tweet);
              } else {
                const scheduledDate = new Date(tweet.scheduled_at);
                if (isNaN(scheduledDate.getTime())) {
                  grouped.drafts.push(tweet);
                } else if (scheduledDate < now) {
                  grouped.overdue.push(tweet);
                } else if (scheduledDate < tomorrow) {
                  grouped.today.push(tweet);
                } else if (scheduledDate < new Date(tomorrow.getTime() + 24 * 60 * 60 * 1000)) {
                  grouped.tomorrow.push(tweet);
                } else if (scheduledDate < nextWeek) {
                  grouped.thisWeek.push(tweet);
                } else {
                  grouped.later.push(tweet);
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
                  const sectionTweets = grouped[section.key];
                  if (sectionTweets.length === 0) return null;

                  const Icon = section.icon;

                  return (
                    <div key={section.key} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <Icon className={`w-5 h-5 ${section.color}`} />
                        <h3 className={`text-lg font-semibold ${section.color}`}>
                          {section.title}
                        </h3>
                        <span className="text-sm text-gray-500">({sectionTweets.length})</span>
                      </div>

                      <div className="space-y-3">
                        {sectionTweets.map((tweet) => (
                          <div
                            key={tweet.id}
                            className="bg-black border border-white/10 rounded-lg p-4 hover:border-blue-500/50 transition"
                          >
                            <div className="flex gap-4">
                              {/* Content */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-4 mb-2">
                                  <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-xs font-bold">
                                      {tweet.brand?.name?.substring(0, 1).toUpperCase() ?? '?'}
                                    </div>
                                    <span className="text-sm font-medium text-white">{tweet.brand?.name ?? 'Unknown'}</span>
                                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(tweet.status)}`}>
                                      {tweet.status || 'unknown'}
                                    </span>
                                  </div>

                                  {tweet.twitter_url && (
                                    <a
                                      href={tweet.twitter_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-xs"
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                      View
                                    </a>
                                  )}
                                </div>

                                <p className="text-gray-300 text-sm mb-2 whitespace-pre-wrap">
                                  {tweet.content || 'No content'}
                                </p>

                                <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
                                  {tweet.scheduled_at && (
                                    <div className="flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {formatDate(tweet.scheduled_at)}
                                    </div>
                                  )}
                                  {tweet.posted_at && (
                                    <div className="flex items-center gap-1">
                                      <CheckCircle className="w-3 h-3" />
                                      Posted {formatDate(tweet.posted_at)}
                                    </div>
                                  )}
                                </div>

                                {tweet.error_message && (
                                  <div className="text-xs text-red-400 mb-3 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" />
                                    {tweet.error_message}
                                  </div>
                                )}

                                <div className="flex items-center gap-2">
                                  {tweet.status !== 'posted' && (
                                    <>
                                      <button
                                        onClick={() => handlePostNow(tweet.id)}
                                        className="text-green-400 hover:text-green-300 text-xs px-3 py-1.5 rounded bg-green-500/10 hover:bg-green-500/20 transition flex items-center gap-1"
                                      >
                                        <Play className="w-3 h-3" />
                                        Post Now
                                      </button>
                                      <button
                                        onClick={() => handleEditTweet(tweet)}
                                        className="text-blue-400 hover:text-blue-300 text-xs px-3 py-1.5 rounded bg-blue-500/10 hover:bg-blue-500/20 transition flex items-center gap-1"
                                      >
                                        <Edit className="w-3 h-3" />
                                        Edit
                                      </button>
                                      <button
                                        onClick={() => handleDeleteTweet(tweet.id)}
                                        className="text-red-400 hover:text-red-300 text-xs px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 transition flex items-center gap-1"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                        Delete
                                      </button>
                                    </>
                                  )}
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
