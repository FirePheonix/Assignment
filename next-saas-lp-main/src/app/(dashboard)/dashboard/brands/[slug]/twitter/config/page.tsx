"use client";

import { ArrowLeft, Twitter, Key, TestTube, AlertCircle, CheckCircle, Loader, RefreshCw, Send, Settings } from "lucide-react";
import Link from "next/link";
import { useState, useEffect, use } from "react";
import { toast } from "sonner";
import { twitterAPI, TwitterConfig } from "@/lib/api/twitter";
import { brandsAPI, Brand } from "@/lib/api/brands";

interface Props {
  params: Promise<{ slug: string }>;
}

// Helper function to get auth token
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export default function TwitterConfigPage({ params }: Props) {
  const { slug } = use(params);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [twitterConfig, setTwitterConfig] = useState<TwitterConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [testLoading, setTestLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [formData, setFormData] = useState({
    api_key: "",
    api_secret: "",
    access_token: "",
    access_token_secret: "",
    bearer_token: "",
  });
  const [testTweet, setTestTweet] = useState("Hello from Gemnar! 🚀 Testing our Twitter integration. #SocialMediaManagement");

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        console.warn('No auth token found, using fallback');
        // Fallback to mock data if no auth token
        const mockBrandData = {
          id: 4,
          name: slug,
          slug: slug,
          has_twitter_config: false,
          description: `Mock brand for ${slug}`
        };
        setBrand(mockBrandData);
        setLoading(false);
        return;
      }

      // Fetch brand data from Django API
      const response = await fetch(`http://localhost:8000/api/brands/${slug}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        }
      });
      
      let brandData;
      if (response.ok) {
        brandData = await response.json();
      } else {
        // Fallback to mock data if Django server is not running
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

      // If Twitter is configured, fetch the Twitter configuration
      if (brandData.has_twitter_config && brandData.id) {
        try {
          const configResponse = await fetch(`http://localhost:8000/api/brands/${brandData.id}/twitter/config/`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Token ${token}`,
            }
          });
          
          if (configResponse.ok) {
            const configData = await configResponse.json();
            setTwitterConfig(configData);
            setFormData({
              api_key: configData.api_key || "",
              api_secret: configData.api_secret || "",
              access_token: configData.access_token || "",
              access_token_secret: configData.access_token_secret || "",
              bearer_token: configData.bearer_token || "",
            });
          }
        } catch (configError) {
          console.error("Failed to load Twitter config:", configError);
        }
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      toast.error("Failed to load Twitter configuration");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brand) return;

    // Validate required fields
    if (!formData.api_key.trim() || !formData.api_secret.trim()) {
      toast.error("API Key and Secret are required");
      return;
    }

    setSaveLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }

      const response = await fetch(`http://localhost:8000/api/brands/${brand.id}/twitter/config/save/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save configuration');
      }

      const result = await response.json();
      toast.success(result.message || "Twitter configuration saved successfully");
      
      // Update brand to show as configured
      setBrand(prev => prev ? { ...prev, has_twitter_config: true } : null);
      
      // Update Twitter config with the saved data
      if (result.username) {
        setTwitterConfig(prev => ({ ...prev, username: result.username }));
      }
    } catch (error: any) {
      console.error("Failed to save Twitter config:", error);
      toast.error(error.message || "Failed to save configuration");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!brand) return;

    setTestLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }

      const response = await fetch(`http://localhost:8000/api/brands/${brand.id}/twitter/test/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        }
      });

      const result = await response.json();

      if (result.success) {
        toast.success(`✅ Connection successful! Authenticated as @${result.username}`);
        setTwitterConfig(prev => ({ ...prev, username: result.username }));
      } else {
        toast.error(`❌ Connection failed: ${result.error}`);
      }
    } catch (error: any) {
      console.error("Failed to test connection:", error);
      toast.error(error.message || "Failed to test connection");
    } finally {
      setTestLoading(false);
    }
  };

  const handleTestTweet = async () => {
    if (!brand) return;

    if (!testTweet.trim()) {
      toast.error("Tweet content is required");
      return;
    }

    if (testTweet.length > 280) {
      toast.error("Tweet is too long (max 280 characters)");
      return;
    }

    setTestLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }

      const response = await fetch(`http://localhost:8000/api/brands/${brand.id}/twitter/test-tweet/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
        body: JSON.stringify({ content: testTweet })
      });

      const result = await response.json();

      if (result.success) {
        toast.success(`✅ Tweet sent successfully! View it: ${result.tweet_url || 'on Twitter'}`);
        setShowTestModal(false);
      } else {
        if (result.error_type === 'authorization') {
          toast.error(`❌ Tweet failed: Authorization error\n\n🔧 Solution: Check your API credentials and permissions`);
        } else if (result.error_type === 'access_level') {
          toast.error(`❌ ${result.error}\n\n🔧 Solution: Upgrade your Twitter API access level to Basic or higher`);
        } else {
          toast.error(`❌ Tweet failed: ${result.error}`);
        }
      }
    } catch (error: any) {
      console.error("Failed to send test tweet:", error);
      toast.error(error.message || "Failed to send tweet");
    } finally {
      setTestLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!brand || !confirm("Are you sure you want to disconnect Twitter? This will remove all Twitter configuration.")) {
      return;
    }

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }

      const response = await fetch(`http://localhost:8000/api/brands/${brand.id}/twitter/disconnect/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to disconnect Twitter');
      }

      const result = await response.json();
      toast.success(result.message || "Twitter disconnected successfully");
      
      // Update state
      setTwitterConfig(null);
      setBrand(prev => prev ? { ...prev, has_twitter_config: false } : null);
      setFormData({
        api_key: "",
        api_secret: "",
        access_token: "",
        access_token_secret: "",
        bearer_token: "",
      });
    } catch (error: any) {
      console.error("Failed to disconnect Twitter:", error);
      toast.error(error.message || "Failed to disconnect");
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
          href={`/dashboard/brands/${brand.slug}`}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-3 flex-1">
          <Twitter className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-3xl font-bold">Twitter Configuration</h1>
            <p className="text-gray-400">Connect {brand.name} to Twitter for automated posting</p>
          </div>
        </div>
        {brand.has_twitter_config && (
          <div className="flex gap-3">
            <button
              onClick={handleTestConnection}
              disabled={testLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              {testLoading ? <Loader className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Test Connection
            </button>
            <button
              onClick={() => setShowTestModal(true)}
              disabled={testLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <TestTube className="w-4 h-4" />
              Test Tweet
            </button>
          </div>
        )}
      </div>

      {/* Connection Status */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              brand.has_twitter_config ? 'bg-green-500/20' : 'bg-red-500/20'
            }`}>
              {brand.has_twitter_config ? (
                <CheckCircle className="w-6 h-6 text-green-400" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-400" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold">
                {brand.has_twitter_config ? 'Connected' : 'Not Connected'}
              </h3>
              <p className="text-gray-400">
                {brand.has_twitter_config 
                  ? `Twitter is connected and ready for posting${twitterConfig?.username ? ` as @${twitterConfig.username}` : ''}`
                  : 'Connect your Twitter account to start posting'
                }
              </p>
            </div>
          </div>
          {brand.has_twitter_config && (
            <button
              onClick={handleDisconnect}
              className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Disconnect
            </button>
          )}
        </div>
      </div>

      {/* Configuration Form */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <Key className="w-6 h-6 text-purple-400" />
          <h2 className="text-xl font-bold">API Configuration</h2>
        </div>

        <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-400 mb-1">How to get Twitter API keys</h4>
              <ol className="text-sm text-blue-300 space-y-1 list-decimal list-inside">
                <li>Visit the <a href="https://developer.twitter.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-200">Twitter Developer Portal</a></li>
                <li>Create a new app or use an existing one</li>
                <li>Generate API keys and access tokens</li>
                <li>Make sure your app has "Read and Write" permissions</li>
                <li>For posting tweets, you need at least "Basic" access level</li>
              </ol>
            </div>
          </div>
        </div>

        <form onSubmit={handleSaveConfig} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">API Key *</label>
              <input
                type="text"
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Your Twitter API Key"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Secret *</label>
              <input
                type="password"
                value={formData.api_secret}
                onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Your Twitter API Secret"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Access Token</label>
              <input
                type="text"
                value={formData.access_token}
                onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Your Access Token (for posting)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Access Token Secret</label>
              <input
                type="password"
                value={formData.access_token_secret}
                onChange={(e) => setFormData({ ...formData, access_token_secret: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Your Access Token Secret"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-2">Bearer Token (Optional)</label>
              <input
                type="text"
                value={formData.bearer_token}
                onChange={(e) => setFormData({ ...formData, bearer_token: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Your Bearer Token (for reading data)"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-6">
            <button
              type="submit"
              disabled={saveLoading}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center gap-2"
            >
              {saveLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Settings className="w-4 h-4" />}
              {saveLoading ? 'Saving...' : 'Save Configuration'}
            </button>
            
            {brand.has_twitter_config && (
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
              >
                {testLoading ? <Loader className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                Test Connection
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Quick Actions */}
      {brand.has_twitter_config && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-4">Quick Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowTestModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send Test Tweet
            </button>
            <Link
              href={`/dashboard/brands/${brand.slug}/twitter`}
              className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <Twitter className="w-4 h-4" />
              View Tweet Queue
            </Link>
            <Link
              href={`/dashboard/brands/${brand.slug}/analytics`}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              View Analytics
            </Link>
          </div>
        </div>
      )}

      {/* Test Tweet Modal */}
      {showTestModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Send Test Tweet</h2>
              <button 
                onClick={() => setShowTestModal(false)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Tweet Content</label>
                <textarea
                  value={testTweet}
                  onChange={(e) => setTestTweet(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 h-24 resize-none"
                  placeholder="What's happening?"
                  maxLength={280}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className={`text-sm ${testTweet.length > 280 ? 'text-red-400' : 'text-gray-400'}`}>
                    {280 - testTweet.length} characters remaining
                  </span>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowTestModal(false)}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTestTweet}
                  disabled={testLoading || testTweet.length > 280 || !testTweet.trim()}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 py-2 px-4 rounded-lg transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {testLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {testLoading ? 'Sending...' : 'Send Tweet'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}