"use client";

import { FileText, CheckCircle, XCircle, Clock, Twitter, ArrowRight } from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";

interface Brand {
  id: number;
  name: string;
  slug: string;
  has_twitter_config: boolean;
}

export default function TwitterHistoryPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const response = await fetch('/api/brands/');
      if (response.ok) {
        const data = await response.json();
        setBrands(data);
      }
    } catch (error) {
      console.error('Error fetching brands:', error);
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

  // Check if any brand has Twitter configured
  const brandsWithTwitter = brands.filter(brand => brand.has_twitter_config);

  if (brandsWithTwitter.length === 0) {
    return (
      <div className="p-8 bg-black min-h-screen">
        <div className="background-pattern-blue" />
        
        <div className="max-w-2xl mx-auto mt-20 relative z-10">
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <FileText className="w-10 h-10 text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">Twitter Setup Required</h1>
            <p className="text-gray-400 mb-6">
              You need to configure Twitter for at least one brand before viewing tweet history.
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
  const tweets = [
    {
      id: 1,
      content: "🚀 Excited to announce our new feature launch! Check it out at gemnar.com #ProductLaunch",
      postedAt: "2025-12-18 14:30:00",
      status: "posted",
      likes: 45,
      retweets: 12,
      replies: 8,
    },
    {
      id: 2,
      content: "Did you know? 80% of our users see results within the first week! Join us today 💪",
      postedAt: "2025-12-18 10:00:00",
      status: "posted",
      likes: 67,
      retweets: 23,
      replies: 15,
    },
    {
      id: 3,
      content: "Behind the scenes: Our team working hard to bring you the best experience 👨‍💻👩‍💻",
      scheduledFor: "2025-12-17 16:00:00",
      status: "failed",
      error: "API rate limit exceeded",
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "posted":
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "posted":
        return "text-green-400";
      case "failed":
        return "text-red-400";
      default:
        return "text-yellow-400";
    }
  };

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Tweet History</h1>
        <p className="text-gray-400">View all past tweets and their performance</p>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mb-6">
        <div className="flex flex-wrap gap-4">
          <select className="bg-black border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500">
            <option>All Statuses</option>
            <option>Posted</option>
            <option>Failed</option>
            <option>Scheduled</option>
          </select>
          
          <input
            type="date"
            className="bg-black border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          
          <input
            type="text"
            placeholder="Search tweets..."
            className="flex-1 min-w-[200px] bg-black border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition">
            Apply Filters
          </button>
        </div>
      </div>

      {/* Tweet History List */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          All Tweets
        </h3>

        <div className="space-y-4">
          {tweets.map((tweet) => (
            <div
              key={tweet.id}
              className="bg-black border border-white/10 rounded-lg p-6 hover:border-purple-500/50 transition"
            >
              <div className="flex items-start gap-4">
                {getStatusIcon(tweet.status)}
                
                <div className="flex-1">
                  <p className="text-white mb-3">{tweet.content}</p>
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    <span className={`font-medium ${getStatusColor(tweet.status)}`}>
                      {tweet.status.charAt(0).toUpperCase() + tweet.status.slice(1)}
                    </span>
                    
                    {tweet.postedAt && (
                      <span className="text-gray-400">
                        Posted: {tweet.postedAt}
                      </span>
                    )}
                    
                    {tweet.status === "posted" && (
                      <>
                        <span className="text-gray-400">❤️ {tweet.likes}</span>
                        <span className="text-gray-400">🔁 {tweet.retweets}</span>
                        <span className="text-gray-400">💬 {tweet.replies}</span>
                      </>
                    )}
                    
                    {tweet.status === "failed" && tweet.error && (
                      <span className="text-red-400 text-xs">
                        Error: {tweet.error}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="text-blue-400 hover:text-blue-300 text-sm px-3 py-1 rounded hover:bg-blue-500/10 transition">
                    View
                  </button>
                  {tweet.status === "failed" && (
                    <button className="text-purple-400 hover:text-purple-300 text-sm px-3 py-1 rounded hover:bg-purple-500/10 transition">
                      Retry
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-6">
          <button className="text-gray-400 hover:text-white px-4 py-2 rounded hover:bg-white/5 transition">
            Previous
          </button>
          <div className="flex items-center gap-2">
            <button className="bg-purple-600 text-white px-3 py-1 rounded">1</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">2</button>
            <button className="text-gray-400 hover:text-white px-3 py-1 rounded hover:bg-white/5 transition">3</button>
          </div>
          <button className="text-gray-400 hover:text-white px-4 py-2 rounded hover:bg-white/5 transition">
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
