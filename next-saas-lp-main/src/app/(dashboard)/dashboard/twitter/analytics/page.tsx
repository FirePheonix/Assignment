"use client";

import { TrendingUp, TrendingDown, Twitter, CheckCircle, XCircle, BarChart3, ArrowRight, Heart, Repeat2, MessageCircle, Eye } from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";
import { twitterAPI, TwitterAnalytics } from "@/lib/api/twitter";
import { useBrands } from "@/hooks/use-brands";
import { toast } from "sonner";

export default function TwitterAnalyticsPage() {
  const { brands = [], isLoading: brandsLoading } = useBrands();
  const [analytics, setAnalytics] = useState<TwitterAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetchAnalytics();
  }, [selectedBrand]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await twitterAPI.getAnalytics(selectedBrand);
      setAnalytics(data);
    } catch (error: any) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading || brandsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  // Check if any brand has Twitter configured
  const brandsWithTwitter = brands.filter(brand => brand.has_twitter_config);

  if (brandsWithTwitter.length === 0) {
    return (
      <div className="p-8 bg-black min-h-screen">
        <div className="background-pattern-blue" />
        
        <div className="max-w-2xl mx-auto mt-20 relative z-10">
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <BarChart3 className="w-10 h-10 text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">Twitter Setup Required</h1>
            <p className="text-gray-400 mb-6">
              You need to configure Twitter for at least one brand before viewing analytics.
              <br />
              Set up your Twitter API credentials to start tracking your social media performance.
            </p>
            
            {brands.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Configure Twitter for your brands:</h3>
                <div className="grid gap-3">
                  {brands.map(brand => (
                    <Link
                      key={brand.id}
                      href={`/dashboard/brands/${brand.slug}/twitter/config`}
                      className="flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/50 rounded-lg transition-all"
                    >
                      <div className="text-left">
                        <div className="font-semibold text-white">{brand.name}</div>
                        <div className="text-sm text-gray-400">Configure Twitter API</div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-purple-400" />
                    </Link>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-gray-400">You need to create a brand first.</p>
                <Link
                  href="/dashboard/brands"
                  className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity"
                >
                  Create Your First Brand
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
          <span className="text-blue-400">Twitter Analytics</span>
        </nav>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-white">Twitter Analytics</h1>
              {selectedBrand && brandsWithTwitter.length > 0 && (
                <span className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-full">
                  {brandsWithTwitter.find(b => b.id === selectedBrand)?.name}
                </span>
              )}
            </div>
            <p className="text-gray-400">
              {selectedBrand 
                ? 'Real-time metrics for selected brand from Twitter API'
                : 'Real-time metrics from Twitter API'}
            </p>
          </div>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium transition"
          >
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
      </div>

      {/* Brand Filter */}
      {brandsWithTwitter.length > 0 && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Select Brand</h2>
            {brandsWithTwitter.length > 1 && (
              <span className="text-sm text-gray-400">{brandsWithTwitter.length} brands connected</span>
            )}
          </div>
          <div className="mt-4">
            <select
              value={selectedBrand || ''}
              onChange={(e) => setSelectedBrand(e.target.value ? Number(e.target.value) : undefined)}
              className="w-full md:w-96 px-4 py-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none cursor-pointer"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23ffffff' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 1rem center',
                paddingRight: '3rem'
              }}
            >
              <option value="">All Brands - Combined Analytics</option>
              {brandsWithTwitter.map(brand => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-2">
              {selectedBrand 
                ? `Showing analytics for ${brandsWithTwitter.find(b => b.id === selectedBrand)?.name || 'selected brand'}`
                : 'Showing combined analytics across all your brands'}
            </p>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-8">
        {/* Total Tweets */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <Twitter className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">{analytics?.total_tweets || 0}</p>
          <p className="text-sm text-gray-400">Total Tweets</p>
        </div>

        {/* Followers */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <Eye className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatNumber(analytics?.total_followers || 0)}</p>
          <p className="text-sm text-gray-400">Followers</p>
        </div>

        {/* Likes */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <Heart className="w-5 h-5 text-red-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatNumber(analytics?.total_likes || 0)}</p>
          <p className="text-sm text-gray-400">Likes</p>
        </div>

        {/* Retweets */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <Repeat2 className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatNumber(analytics?.total_retweets || 0)}</p>
          <p className="text-sm text-gray-400">Retweets</p>
        </div>

        {/* Replies */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <MessageCircle className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatNumber(analytics?.total_replies || 0)}</p>
          <p className="text-sm text-gray-400">Replies</p>
        </div>

        {/* Engagement Rate */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-5 h-5 text-yellow-400" />
          </div>
          <p className="text-2xl font-bold text-white">{analytics?.engagement_rate.toFixed(2) || 0}%</p>
          <p className="text-sm text-gray-400">Engagement Rate</p>
        </div>
      </div>

      {/* Brand Performance */}
      {analytics && analytics.brands && analytics.brands.length > 0 && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-6">Brand Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analytics.brands.map(brand => (
              <div key={brand.id} className="bg-black border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-semibold">{brand.name}</h3>
                  <span className="text-xs text-gray-500">@{brand.username}</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                  <div className="bg-[#1a1a1a] rounded p-2">
                    <div className="text-gray-400 text-xs">Followers</div>
                    <div className="text-white font-semibold">{formatNumber(brand.followers)}</div>
                  </div>
                  <div className="bg-[#1a1a1a] rounded p-2">
                    <div className="text-gray-400 text-xs">Following</div>
                    <div className="text-white font-semibold">{formatNumber(brand.following)}</div>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tweets:</span>
                    <span className="text-white">{brand.total_tweets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Likes:</span>
                    <span className="text-white">{formatNumber(brand.total_likes)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Retweets:</span>
                    <span className="text-white">{formatNumber(brand.total_retweets)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Engagement:</span>
                    <span className="text-yellow-400 font-semibold">{brand.engagement_rate.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Performing Tweets */}
      {analytics && analytics.top_performing && analytics.top_performing.length > 0 && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            Top Performing Tweets
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {analytics.top_performing.slice(0, 6).map((tweet) => (
              <div key={tweet.id} className="bg-black border border-white/10 rounded-lg p-4 hover:border-blue-500/50 transition">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-xs font-bold">
                      {tweet.brand_name.substring(0, 1).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-gray-400">{tweet.brand_name}</span>
                  </div>
                  {tweet.twitter_url && (
                    <a
                      href={tweet.twitter_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1"
                    >
                      <Twitter className="w-3 h-3" />
                      View
                    </a>
                  )}
                </div>
                
                <p className="text-white text-sm mb-3 line-clamp-3">{tweet.content}</p>
                
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Heart className="w-3 h-3 text-red-400" />
                    <div className="flex flex-col">
                      <span>{formatNumber(tweet.metrics.likes)}</span>
                      {tweet.metrics.verified_likes !== undefined && tweet.metrics.verified_likes !== tweet.metrics.likes && (
                        <span className="text-green-400 text-[10px]">✓ {formatNumber(tweet.metrics.verified_likes)} verified</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Repeat2 className="w-3 h-3 text-green-400" />
                    <span>{formatNumber(tweet.metrics.retweets)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <MessageCircle className="w-3 h-3 text-blue-400" />
                    <span>{formatNumber(tweet.metrics.replies)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Twitter className="w-3 h-3 text-purple-400" />
                    <span>{formatNumber(tweet.metrics.quotes)}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">{formatDate(tweet.posted_at)}</span>
                  <span className="text-yellow-400 font-medium">{tweet.metrics.engagement_rate}% engagement</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Tweets Table */}
      {analytics && analytics.tweets && analytics.tweets.length > 0 && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">All Tweets</h2>
          <div className="space-y-3">
            {analytics.tweets.map((tweet) => (
              <div key={tweet.id} className="bg-black border border-white/10 rounded-lg p-4 hover:border-blue-500/50 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-5 h-5 rounded bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-xs font-bold">
                        {tweet.brand_name.substring(0, 1).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-gray-400">{tweet.brand_name}</span>
                      <span className="text-xs text-gray-500">•</span>
                      <span className="text-xs text-gray-500">{formatDate(tweet.posted_at)}</span>
                    </div>
                    
                    <p className="text-white text-sm mb-3">{tweet.content}</p>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <div className="flex items-center gap-1">
                        <Heart className="w-3 h-3 text-red-400" />
                        <div className="flex items-center gap-1">
                          <span>{formatNumber(tweet.metrics.likes)}</span>
                          {tweet.metrics.verified_likes !== undefined && tweet.metrics.verified_likes !== tweet.metrics.likes && (
                            <span className="text-green-400 text-[10px]">(✓{formatNumber(tweet.metrics.verified_likes)})</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Repeat2 className="w-3 h-3 text-green-400" />
                        <span>{formatNumber(tweet.metrics.retweets)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MessageCircle className="w-3 h-3 text-blue-400" />
                        <span>{formatNumber(tweet.metrics.replies)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Twitter className="w-3 h-3 text-purple-400" />
                        <span>{formatNumber(tweet.metrics.quotes)}</span>
                      </div>
                      <div className="ml-auto text-yellow-400 font-medium">
                        {tweet.metrics.engagement_rate.toFixed(2)}% engagement
                      </div>
                    </div>
                  </div>
                  
                  {tweet.twitter_url && (
                    <a
                      href={tweet.twitter_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-xs shrink-0"
                    >
                      <Twitter className="w-3 h-3" />
                      View on X
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Data State */}
      {analytics && analytics.total_tweets === 0 && (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
          <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Analytics Data Yet</h3>
          <p className="text-gray-400 mb-6">
            {analytics.message || 'Start posting tweets to see analytics data here.'}
          </p>
          <Link
            href="/dashboard/twitter/queue"
            className="inline-block bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 text-white px-6 py-3 rounded-lg font-medium transition"
          >
            Create Your First Tweet
          </Link>
        </div>
      )}
    </div>
  );
}
