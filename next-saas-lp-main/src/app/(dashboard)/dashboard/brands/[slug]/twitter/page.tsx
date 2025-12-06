"use client";

import {
  ArrowLeft,
  Twitter,
  Calendar,
  Clock,
  Image as ImageIcon,
  Sparkles,
  Plus,
  Send,
  Trash2,
  BarChart3,
  Eye,
  RefreshCw,
  Settings,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { useState, useEffect, use } from "react";
import { toast } from "sonner";

interface Brand {
  id: number;
  name: string;
  slug: string;
  has_twitter_config: boolean;
  description?: string;
}

interface TwitterQueue {
  tweets: QueuedTweet[];
  stats: {
    total: number;
    scheduled: number;
    posted: number;
  };
}

interface QueuedTweet {
  id: number;
  content: string;
  scheduled_at?: string;
  status: 'draft' | 'scheduled' | 'posted' | 'failed';
  media_urls: string[];
  created_at: string;
}

interface Props {
  params: Promise<{ slug: string }>;
}

export default function TwitterQueuePage({ params }: Props) {
  const { slug } = use(params);
  const [activeTab, setActiveTab] = useState<"queue" | "drafts" | "scheduled">("queue");
  const [brand, setBrand] = useState<Brand | null>(null);
  const [queue, setQueue] = useState<TwitterQueue | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [newTweet, setNewTweet] = useState({
    content: "",
    scheduled_at: "",
    media_urls: [] as string[],
  });

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      // Fetch brand data from Django API
      const response = await fetch(`/api/brands/${slug}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('auth_token')}`,
        }
      });
      
      if (!response.ok) {
        // Fallback to mock data if Django server is not running
        console.warn('Django API not available, using mock data');
        const mockBrandData = {
          id: 1,
          name: slug,
          slug: slug,
          has_twitter_config: false,
          description: `Mock brand for ${slug}`
        };
        setBrand(mockBrandData);
        return;
      }
      
      const brandData = await response.json();
      setBrand(brandData);

      // If Twitter is configured, fetch queue data (placeholder for now)
      if (brandData.has_twitter_config) {
        // TODO: Implement actual queue fetching when backend endpoints are ready
        setQueue({ tweets: [], stats: { total: 0, scheduled: 0, posted: 0 } });
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      toast.error("Failed to load brand data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTweet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brand) return;

    if (!newTweet.content.trim()) {
      toast.error("Tweet content is required");
      return;
    }

    if (newTweet.content.length > 280) {
      toast.error("Tweet is too long (max 280 characters)");
      return;
    }

    setCreateLoading(true);
    try {
      // TODO: Implement actual tweet creation when backend endpoints are ready
      toast.success("Tweet functionality coming soon!");
      setShowCreateModal(false);
      setNewTweet({ content: "", scheduled_at: "", media_urls: [] });
    } catch (error: any) {
      console.error("Failed to create tweet:", error);
      toast.error(error.message || "Failed to create tweet");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteTweet = async (tweetId: number) => {
    if (!confirm("Are you sure you want to delete this tweet?")) return;
    toast.success("Delete functionality coming soon!");
  };

  const handlePostNow = async (tweetId: number) => {
    if (!confirm("Post this tweet now?")) return;
    toast.success("Post now functionality coming soon!");
  };

  const generateAITweets = async () => {
    if (!brand) return;
    toast.success("AI tweet generation coming soon!");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!brand) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold mb-2">Brand not found</h2>
        <Link href="/dashboard/brands" className="text-blue-400 hover:underline">
          ← Back to Brands
        </Link>
      </div>
    );
  }

  // Redirect to Twitter configuration if not set up
  if (!brand.has_twitter_config) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <Link
            href={`/dashboard/brands/${brand.slug}`}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3">
            <Twitter className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold">Twitter Setup Required</h1>
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <h3 className="text-xl font-bold mb-2">Twitter Not Configured</h3>
          <p className="text-gray-400 mb-6">
            You must configure and verify your Twitter API credentials before accessing Twitter features.
            <br />
            Configure your API keys, test the connection, and verify it's working.
          </p>
          <div className="space-y-3">
            <Link
              href={`/dashboard/brands/${brand.slug}/twitter/config`}
              className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity"
            >
              Configure Twitter API
            </Link>
            <p className="text-sm text-gray-500">
              Need Twitter API keys? <a href="https://developer.twitter.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Get them from Twitter Developer Portal</a>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const tweets = queue?.tweets || [];

  const filteredTweets = tweets.filter((tweet) => {
    if (activeTab === "queue") return tweet.status === "queued";
    if (activeTab === "drafts") return tweet.status === "draft";  
    if (activeTab === "scheduled") return tweet.status === "scheduled";
    return false;
  });

  const stats = queue?.stats || {
    total_queued: 0,
    total_scheduled: 0,
    total_drafts: 0,
    total_posted: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href={`/dashboard/brands/${brand.slug}`}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-3 flex-1">
          <Twitter className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-3xl font-bold">Twitter Queue</h1>
            <p className="text-gray-400">Manage and schedule tweets for {brand.name}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Link
            href={`/dashboard/brands/${brand.slug}/twitter/config`}
            className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Create Tweet
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">{stats.total_queued}</div>
          <div className="text-sm text-gray-400">In Queue</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">{stats.total_scheduled}</div>
          <div className="text-sm text-gray-400">Scheduled</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">{stats.total_drafts}</div>
          <div className="text-sm text-gray-400">Drafts</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold">{stats.total_posted}</div>
          <div className="text-sm text-gray-400">Total Posted</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        <button
          onClick={() => setActiveTab("queue")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "queue"
              ? "border-b-2 border-purple-500 text-white"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          Queue
        </button>
        <button
          onClick={() => setActiveTab("scheduled")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "scheduled"
              ? "border-b-2 border-purple-500 text-white"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          Scheduled
        </button>
        <button
          onClick={() => setActiveTab("drafts")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "drafts"
              ? "border-b-2 border-purple-500 text-white"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          Drafts
        </button>
      </div>

      {/* Tweets List */}
      <div className="space-y-4">
        {filteredTweets.map((tweet) => (
          <div
            key={tweet.id}
            className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors"
          >
            {/* Tweet Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <p className="text-base mb-3">{tweet.content}</p>
                {tweet.media_urls && tweet.media_urls.length > 0 && (
                  <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                    <ImageIcon className="w-4 h-4" />
                    <span>{tweet.media_urls.length} media file(s) attached</span>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                  <Eye className="w-5 h-5 text-gray-400" />
                </button>
                <button 
                  onClick={() => handleDeleteTweet(tweet.id)}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5 text-red-400" />
                </button>
              </div>
            </div>

            {/* Tweet Meta */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm text-gray-400">
                {tweet.scheduled_at && (
                  <>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>
                        {new Date(tweet.scheduled_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>
                        {new Date(tweet.scheduled_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </>
                )}
                <span className={`px-2 py-1 rounded-full text-xs ${
                  tweet.status === "draft" ? "bg-gray-500/20 text-gray-400" :
                  tweet.status === "scheduled" ? "bg-blue-500/20 text-blue-400" :
                  tweet.status === "queued" ? "bg-yellow-500/20 text-yellow-400" :
                  "bg-green-500/20 text-green-400"
                }`}>
                  {tweet.status === "queued" ? "In Queue" : tweet.status}
                </span>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {tweet.status === "draft" && (
                  <button className="bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Schedule
                  </button>
                )}
                {(tweet.status === "queued" || tweet.status === "scheduled") && (
                  <button 
                    onClick={() => handlePostNow(tweet.id)}
                    className="bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Post Now
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {filteredTweets.length === 0 && (
          <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
              <Clock className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-bold mb-2">No tweets in {activeTab}</h3>
            <p className="text-gray-400 mb-6">
              Create your first tweet to get started
            </p>
            <button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity">
              Create Tweet
            </button>
          </div>
        )}
      </div>

      {/* AI Generate Section */}
      <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-purple-500/20 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold mb-1">AI Tweet Generator</h3>
            <p className="text-sm text-gray-400 mb-4">
              Generate engaging tweets automatically based on your brand voice
              and trending topics
            </p>
            <div className="flex gap-2">
              <button 
                onClick={generateAITweets}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Generate Tweets
              </button>
              <button className="bg-white/5 border border-white/10 hover:bg-white/10 px-4 py-2 rounded-lg text-sm transition-colors">
                Configure AI
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Create Tweet Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Create New Tweet</h2>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTweet} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Tweet Content *</label>
                <textarea
                  value={newTweet.content}
                  onChange={(e) => setNewTweet({ ...newTweet, content: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-24 resize-none"
                  placeholder="What's happening?"
                  maxLength={280}
                  required
                />
                <div className="flex justify-between items-center mt-1">
                  <span className={`text-sm ${newTweet.content.length > 280 ? 'text-red-400' : 'text-gray-400'}`}>
                    {280 - newTweet.content.length} characters remaining
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Schedule (Optional)</label>
                <input
                  type="datetime-local"
                  value={newTweet.scheduled_at}
                  onChange={(e) => setNewTweet({ ...newTweet, scheduled_at: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  min={new Date().toISOString().slice(0, 16)}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Leave empty to add to queue for immediate posting
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading || newTweet.content.length > 280 || !newTweet.content.trim()}
                  className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 py-2 px-4 rounded-lg transition-opacity font-medium"
                >
                  {createLoading ? "Creating..." : newTweet.scheduled_at ? "Schedule" : "Add to Queue"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
