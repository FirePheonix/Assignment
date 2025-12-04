"use client";

import { Settings, Save, Twitter, ArrowRight, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";

interface Brand {
  id: number;
  name: string;
  slug: string;
  has_twitter_config: boolean;
}

export default function TwitterConfigPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      const response = await fetch('/api/brands/', {
        headers
      });
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

  return (
    <div className="p-8 bg-black min-h-screen">
      <div className="background-pattern-blue" />
      
      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Twitter Configuration</h1>
          <p className="text-gray-400">Configure Twitter settings for your brands</p>
        </div>

        {/* Info Notice */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 mt-1" />
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Brand-Specific Configuration</h3>
              <p className="text-blue-300/80 text-sm">
                Twitter is configured on a per-brand basis. Each brand needs its own Twitter API credentials 
                to enable posting, scheduling, and analytics. Choose a brand below to configure its Twitter integration.
              </p>
            </div>
          </div>
        </div>

        {brands.length > 0 ? (
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Your Brands</h2>
            <div className="grid gap-4">
              {brands.map(brand => (
                <Link
                  key={brand.id}
                  href={`/dashboard/brands/${brand.slug}/twitter/config`}
                  className="flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/50 rounded-lg transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                      {brand.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold text-white">{brand.name}</div>
                      <div className="text-sm text-gray-400">
                        {brand.has_twitter_config ? (
                          <span className="text-green-400">✓ Twitter Configured</span>
                        ) : (
                          <span className="text-yellow-400">⚠ Twitter Not Configured</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {brand.has_twitter_config ? (
                      <span className="text-sm px-3 py-1 bg-green-500/20 text-green-400 rounded-full">
                        Active
                      </span>
                    ) : (
                      <span className="text-sm px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full">
                        Setup Required
                      </span>
                    )}
                    <ArrowRight className="w-5 h-5 text-purple-400" />
                  </div>
                </Link>
              ))}
            </div>

            {/* Summary Stats */}
            <div className="mt-6 pt-6 border-t border-white/10">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-white">{brands.length}</div>
                  <div className="text-sm text-gray-400">Total Brands</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">
                    {brands.filter(b => b.has_twitter_config).length}
                  </div>
                  <div className="text-sm text-gray-400">Configured</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {brands.filter(b => !b.has_twitter_config).length}
                  </div>
                  <div className="text-sm text-gray-400">Need Setup</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-purple-500/20 flex items-center justify-center">
              <Twitter className="w-10 h-10 text-purple-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-4">No Brands Found</h2>
            <p className="text-gray-400 mb-6">
              You need to create a brand before configuring Twitter integration.
              <br />
              Brands allow you to manage separate Twitter accounts and campaigns.
            </p>
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
  );
}
