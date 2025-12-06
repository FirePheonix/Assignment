"use client";

import { ArrowLeft, TrendingUp, Users, MessageCircle, Heart, Repeat, BarChart3, Calendar, Eye } from "lucide-react";
import Link from "next/link";
import { useState, useEffect, use } from "react";
import { toast } from "sonner";
import { twitterAPI, TwitterAnalytics } from "@/lib/api/twitter";
import { brandsAPI, Brand } from "@/lib/api/brands";

interface Props {
  params: Promise<{ slug: string }>;
}

export default function TwitterAnalyticsPage({ params }: Props) {
  const { slug } = use(params);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [analytics, setAnalytics] = useState<TwitterAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    loadData();
  }, [slug, timeRange]);

  const loadData = async () => {
    try {
      // Try fetching brand data from API first
      const response = await fetch(`/api/brands/${slug}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('authToken')}`,
        }
      });
      
      let brandData;
      if (response.ok) {
        brandData = await response.json();
      } else {
        // Fallback to mock data
        console.warn('Django API not available, using mock data');
        brandData = {
          id: 1,
          name: slug,
          slug: slug,
          has_twitter_config: false,
          description: `Mock brand for ${slug}`
        };
      }
      
      setBrand(brandData);
      
      // Mock analytics data
      const mockAnalytics = {
        followers_count: 1250,
        following_count: 180,
        tweets_count: 45,
        total_impressions: 15680,
        total_engagements: 892,
        engagement_rate: 5.69,
        top_tweets: [
          {
            id: '1',
            text: 'Just launched our new feature! 🚀',
            impressions: 2340,
            likes: 45,
            retweets: 12,
            replies: 8,
            created_at: new Date().toISOString()
          },
          {
            id: '2', 
            text: 'Thanks to all our amazing users! ❤️',
            impressions: 1890,
            likes: 67,
            retweets: 8,
            replies: 15,
            created_at: new Date(Date.now() - 86400000).toISOString()
          }
        ],
        daily_stats: Array.from({ length: 7 }, (_, i) => ({
          date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
          impressions: Math.floor(Math.random() * 1000) + 500,
          engagements: Math.floor(Math.random() * 100) + 20,
          followers: 1250 - i * 2
        })).reverse()
      };
      
      setAnalytics(mockAnalytics);
    } catch (error) {
      console.error("Failed to load analytics:", error);
      toast.error("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href={`/dashboard/brands/${brand.slug}/twitter`}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-3 flex-1">
          <BarChart3 className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-3xl font-bold">Twitter Analytics</h1>
            <p className="text-gray-400">Performance insights for {brand.name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {['7d', '30d', '90d'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range as '7d' | '30d' | '90d')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === range 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-white/5 border border-white/10 hover:bg-white/10'
              }`}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {analytics && (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <Eye className="w-5 h-5 text-blue-400" />
                <span className={`text-sm px-2 py-1 rounded-full ${
                  analytics.overview.impressions_change >= 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {analytics.overview.impressions_change >= 0 ? '+' : ''}{analytics.overview.impressions_change}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400">Impressions</h3>
              <p className="text-2xl font-bold">{analytics.overview.total_impressions.toLocaleString()}</p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-purple-400" />
                <span className={`text-sm px-2 py-1 rounded-full ${
                  analytics.overview.engagements_change >= 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {analytics.overview.engagements_change >= 0 ? '+' : ''}{analytics.overview.engagements_change}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400">Engagements</h3>
              <p className="text-2xl font-bold">{analytics.overview.total_engagements.toLocaleString()}</p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <Users className="w-5 h-5 text-green-400" />
                <span className={`text-sm px-2 py-1 rounded-full ${
                  analytics.overview.followers_change >= 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {analytics.overview.followers_change >= 0 ? '+' : ''}{analytics.overview.followers_change}
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400">Followers</h3>
              <p className="text-2xl font-bold">{analytics.overview.total_followers.toLocaleString()}</p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <BarChart3 className="w-5 h-5 text-orange-400" />
                <span className={`text-sm px-2 py-1 rounded-full ${
                  analytics.overview.engagement_rate_change >= 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {analytics.overview.engagement_rate_change >= 0 ? '+' : ''}{analytics.overview.engagement_rate_change}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400">Engagement Rate</h3>
              <p className="text-2xl font-bold">{analytics.overview.engagement_rate}%</p>
            </div>
          </div>

          {/* Top Performing Tweets */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-6">Top Performing Tweets</h2>
            <div className="space-y-4">
              {analytics.top_tweets.map((tweet, index) => (
                <div
                  key={tweet.id}
                  className="bg-white/5 border border-white/10 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <p className="text-base mb-2">{tweet.content}</p>
                      <p className="text-sm text-gray-400">
                        {new Date(tweet.posted_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="bg-purple-600 text-white px-2 py-1 rounded-full text-xs font-bold">
                        #{index + 1}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-blue-400" />
                      <span>{tweet.impressions.toLocaleString()} impressions</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Heart className="w-4 h-4 text-red-400" />
                      <span>{tweet.likes} likes</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Repeat className="w-4 h-4 text-green-400" />
                      <span>{tweet.retweets} retweets</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MessageCircle className="w-4 h-4 text-purple-400" />
                      <span>{tweet.replies} replies</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Engagement Trends Chart */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-6">Engagement Trends</h2>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                <p>Chart visualization would go here</p>
                <p className="text-sm">Integration with charting library needed</p>
              </div>
            </div>
          </div>

          {/* Best Posting Times */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Best Times to Post</h3>
              <div className="space-y-3">
                {analytics.best_times.map((time, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-gray-400">{time.time}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-white/10 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${time.engagement_rate}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{time.engagement_rate}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Content Performance</h3>
              <div className="space-y-3">
                {analytics.content_types.map((type, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-gray-400">{type.type}</span>
                    <div className="text-right">
                      <p className="text-sm font-medium">{type.avg_engagement} avg engagement</p>
                      <p className="text-xs text-gray-400">{type.count} tweets</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-6">Recent Activity</h2>
            <div className="space-y-4">
              {analytics.recent_activity.map((activity, index) => (
                <div key={index} className="flex items-center gap-4 p-3 bg-white/5 rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                    {activity.type === 'tweet' && <MessageCircle className="w-4 h-4" />}
                    {activity.type === 'like' && <Heart className="w-4 h-4" />}
                    {activity.type === 'retweet' && <Repeat className="w-4 h-4" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm">{activity.description}</p>
                    <p className="text-xs text-gray-400">{new Date(activity.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {!analytics && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
          <BarChart3 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-bold mb-2">No Analytics Data</h3>
          <p className="text-gray-400 mb-6">
            Start posting tweets to see analytics data here
          </p>
          <Link
            href={`/dashboard/brands/${brand.slug}/twitter`}
            className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity"
          >
            Go to Tweet Queue
          </Link>
        </div>
      )}
    </div>
  );
}
