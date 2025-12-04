"use client";

import { Twitter, Instagram, BarChart3, Settings, AlertCircle, CheckCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState, useEffect, use } from "react";

interface Brand {
  id: number;
  name: string;
  slug: string;
  description?: string;
  has_twitter_config: boolean;
  has_instagram_config: boolean;
}

interface Props {
  params: Promise<{ slug: string }>;
}

export default function BrandDetailPage({ params }: Props) {
  const { slug } = use(params);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrand();
  }, [slug]);

  const fetchBrand = async () => {
    try {
      const response = await fetch(`/api/brands/${slug}`);
      if (!response.ok) {
        // Fallback to mock data
        console.warn('Django API not available, using mock data');
        const mockBrand = {
          id: 1,
          name: slug,
          slug: slug,
          description: `Mock brand for ${slug}`,
          has_twitter_config: false,
          has_instagram_config: false
        };
        setBrand(mockBrand);
        return;
      }
      
      const data = await response.json();
      setBrand(data);
    } catch (error) {
      console.error('Error fetching brand:', error);
      // Fallback to mock data on error
      const mockBrand = {
        id: 1,
        name: slug,
        slug: slug,
        description: `Mock brand for ${slug}`,
        has_twitter_config: false,
        has_instagram_config: false
      };
      setBrand(mockBrand);
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
          href="/dashboard/brands"
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{brand.name}</h1>
          {brand.description && (
            <p className="text-gray-400 mt-1">{brand.description}</p>
          )}
        </div>
        <Link
          href={`/dashboard/brands/${brand.slug}/settings`}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <Settings className="w-5 h-5 text-gray-400" />
        </Link>
      </div>

      {/* Quick Links Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Twitter Card */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className={`p-3 rounded-lg transition-colors ${
              brand.has_twitter_config 
                ? 'bg-blue-500/20' 
                : 'bg-gray-500/20'
            }`}>
              <Twitter className={`w-6 h-6 ${
                brand.has_twitter_config ? 'text-blue-400' : 'text-gray-400'
              }`} />
            </div>
            <div>
              <h3 className="font-bold text-lg">Twitter</h3>
              <p className="text-sm text-gray-400">
                {brand.has_twitter_config ? 'Manage tweets & queue' : 'Configure Twitter API'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-400 text-sm">
              {brand.has_twitter_config ? 'API configured' : 'Setup required'}
            </span>
            {brand.has_twitter_config ? (
              <span className="flex items-center gap-1 text-green-400 text-sm">
                <CheckCircle className="w-4 h-4" />
                Active
              </span>
            ) : (
              <span className="flex items-center gap-1 text-yellow-400 text-sm">
                <AlertCircle className="w-4 h-4" />
                Setup
              </span>
            )}
          </div>

          <div className="flex gap-2">
            {brand.has_twitter_config ? (
              <>
                <Link
                  href={`/dashboard/brands/${brand.slug}/twitter`}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-center py-2 px-3 rounded-lg text-sm font-medium transition-colors"
                >
                  Manage
                </Link>
                <Link
                  href={`/dashboard/brands/${brand.slug}/twitter/config`}
                  className="px-3 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-sm transition-colors"
                >
                  Settings
                </Link>
              </>
            ) : (
              <Link
                href={`/dashboard/brands/${brand.slug}/twitter/config`}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white text-center py-2 px-3 rounded-lg text-sm font-medium transition-opacity"
              >
                Setup Twitter
              </Link>
            )}
          </div>
        </div>

        {/* Instagram Card */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className={`p-3 rounded-lg transition-colors ${
              brand.has_instagram_config 
                ? 'bg-pink-500/20' 
                : 'bg-gray-500/20'
            }`}>
              <Instagram className={`w-6 h-6 ${
                brand.has_instagram_config ? 'text-pink-400' : 'text-gray-400'
              }`} />
            </div>
            <div>
              <h3 className="font-bold text-lg">Instagram</h3>
              <p className="text-sm text-gray-400">
                {brand.has_instagram_config ? 'Manage posts & reels' : 'Configure Instagram API'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-400 text-sm">
              {brand.has_instagram_config ? 'API configured' : 'Setup required'}
            </span>
            {brand.has_instagram_config ? (
              <span className="flex items-center gap-1 text-green-400 text-sm">
                <CheckCircle className="w-4 h-4" />
                Active
              </span>
            ) : (
              <span className="flex items-center gap-1 text-yellow-400 text-sm">
                <AlertCircle className="w-4 h-4" />
                Setup
              </span>
            )}
          </div>

          <div className="flex gap-2">
            {brand.has_instagram_config ? (
              <>
                <Link
                  href={`/dashboard/brands/${brand.slug}/instagram`}
                  className="flex-1 bg-pink-600 hover:bg-pink-700 text-white text-center py-2 px-3 rounded-lg text-sm font-medium transition-colors"
                >
                  Manage
                </Link>
                <Link
                  href={`/dashboard/brands/${brand.slug}/instagram/config`}
                  className="px-3 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-sm transition-colors"
                >
                  Settings
                </Link>
              </>
            ) : (
              <Link
                href={`/dashboard/brands/${brand.slug}/instagram/config`}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white text-center py-2 px-3 rounded-lg text-sm font-medium transition-opacity"
              >
                Setup Instagram
              </Link>
            )}
          </div>
        </div>

        {/* Analytics Card */}
        <Link
          href={`/dashboard/brands/${brand.slug}/analytics`}
          className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-purple-500/20 rounded-lg group-hover:bg-purple-500/30 transition-colors">
              <BarChart3 className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Analytics</h3>
              <p className="text-sm text-gray-400">View performance</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Cross-platform insights</span>
            <span className="text-blue-400">View stats</span>
          </div>
        </Link>
      </div>

      {/* Configuration Status */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h2 className="text-lg font-bold mb-4">Configuration Status</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div className="flex items-center gap-3">
              <Twitter className={`w-5 h-5 ${brand.has_twitter_config ? 'text-blue-400' : 'text-gray-400'}`} />
              <span>Twitter Integration</span>
            </div>
            {brand.has_twitter_config ? (
              <span className="flex items-center gap-1 text-green-400 text-sm">
                <CheckCircle className="w-4 h-4" />
                Ready
              </span>
            ) : (
              <Link
                href={`/dashboard/brands/${brand.slug}/twitter/config`}
                className="text-yellow-400 hover:text-yellow-300 text-sm flex items-center gap-1"
              >
                <AlertCircle className="w-4 h-4" />
                Setup Required
              </Link>
            )}
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div className="flex items-center gap-3">
              <Instagram className={`w-5 h-5 ${brand.has_instagram_config ? 'text-pink-400' : 'text-gray-400'}`} />
              <span>Instagram Integration</span>
            </div>
            {brand.has_instagram_config ? (
              <span className="flex items-center gap-1 text-green-400 text-sm">
                <CheckCircle className="w-4 h-4" />
                Ready
              </span>
            ) : (
              <span className="text-gray-400 text-sm flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                Coming Soon
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}