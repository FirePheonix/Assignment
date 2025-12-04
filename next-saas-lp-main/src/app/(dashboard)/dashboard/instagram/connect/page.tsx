"use client";

import { Instagram, CheckCircle, XCircle, ExternalLink, RefreshCw } from "lucide-react";
import { useState, useEffect } from "react";
import { useBrands } from "@/hooks/use-brands";
import { instagramAPI } from "@/lib/api/instagram";
import Link from "next/link";
import { toast } from "sonner";

interface BrandWithStatus {
  id: number;
  name: string;
  slug: string;
  description?: string;
  organization_name?: string | null;
  instagram_connected: boolean;
  instagram_username?: string;
  instagram_user_id?: string;
  connected_at?: string;
  isConnecting?: boolean;
}

export default function InstagramConnectPage() {
  const { brands: initialBrands, isLoading: brandsLoading } = useBrands();
  const [brandsWithStatus, setBrandsWithStatus] = useState<BrandWithStatus[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load Instagram status for all brands
  useEffect(() => {
    const loadBrandStatuses = async () => {
      if (!initialBrands.length) return;

      const brandsWithStatusData = await Promise.all(
        initialBrands.map(async (brand) => {
          try {
            const status = await instagramAPI.getOAuthStatus(brand.id);
            return {
              ...brand,
              instagram_connected: status.connected,
              instagram_username: status.instagram_username,
              instagram_user_id: status.instagram_user_id,
              connected_at: status.connected_at,
            };
          } catch (error) {
            return {
              ...brand,
              instagram_connected: false,
            };
          }
        })
      );

      setBrandsWithStatus(brandsWithStatusData);
    };

    loadBrandStatuses();
  }, [initialBrands]);

  const handleConnect = async (brandId: number) => {
    setBrandsWithStatus(prev => 
      prev.map(b => b.id === brandId ? { ...b, isConnecting: true } : b)
    );

    try {
      localStorage.setItem('instagram_connecting_brand_id', brandId.toString());
      const { oauth_url } = await instagramAPI.startOAuth(brandId);
      
      const popup = window.open(oauth_url, 'instagram_oauth', 'width=600,height=700');
      
      if (!popup) {
        toast.error('Please allow popups to connect Instagram');
        return;
      }

      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          setBrandsWithStatus(prev => 
            prev.map(b => b.id === brandId ? { ...b, isConnecting: false } : b)
          );
          setTimeout(() => refreshBrandStatus(brandId), 1000);
        }
      }, 1000);
    } catch (error: any) {
      toast.error(error.message || 'Failed to start Instagram authentication');
      setBrandsWithStatus(prev => 
        prev.map(b => b.id === brandId ? { ...b, isConnecting: false } : b)
      );
    }
  };

  const handleDisconnect = async (brandId: number) => {
    if (!confirm('Are you sure you want to disconnect this Instagram account?')) {
      return;
    }

    try {
      await instagramAPI.disconnect(brandId);
      toast.success('Instagram account disconnected');
      refreshBrandStatus(brandId);
    } catch (error: any) {
      toast.error(error.message || 'Failed to disconnect Instagram account');
    }
  };

  const refreshBrandStatus = async (brandId: number) => {
    try {
      const status = await instagramAPI.getOAuthStatus(brandId);
      setBrandsWithStatus(prev =>
        prev.map(b =>
          b.id === brandId
            ? {
                ...b,
                instagram_connected: status.connected,
                instagram_username: status.instagram_username,
                instagram_user_id: status.instagram_user_id,
                connected_at: status.connected_at,
              }
            : b
        )
      );
    } catch (error) {
      console.error('Failed to refresh brand status:', error);
    }
  };

  const refreshAllStatuses = async () => {
    setIsRefreshing(true);
    await Promise.all(brandsWithStatus.map(b => refreshBrandStatus(b.id)));
    setIsRefreshing(false);
    toast.success('Instagram statuses refreshed');
  };

  // Group brands by organization
  const groupedBrands = brandsWithStatus.reduce((acc, brand) => {
    const orgName = brand.organization_name || 'Personal';
    if (!acc[orgName]) {
      acc[orgName] = [];
    }
    acc[orgName].push(brand);
    return acc;
  }, {} as Record<string, BrandWithStatus[]>);

  const connectedCount = brandsWithStatus.filter(b => b.instagram_connected).length;

  return (
    <div className="p-8 bg-black min-h-screen">
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-8 relative z-10">
        <nav className="text-sm text-gray-400 mb-2">
          <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
          <span className="mx-2">→</span>
          <span className="text-purple-400">Instagram Connect</span>
        </nav>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Instagram Connections</h1>
            <p className="text-gray-400">
              {connectedCount} of {brandsWithStatus.length} brands connected
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={refreshAllStatuses}
              disabled={isRefreshing}
              className="bg-white/5 border border-white/10 hover:bg-white/10 text-white py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <Link
              href="/dashboard/instagram/queue"
              className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg transition-colors"
            >
              View Queue
            </Link>
          </div>
        </div>
      </div>

      {brandsLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading brands...</p>
        </div>
      ) : brandsWithStatus.length === 0 ? (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
          <Instagram className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">No Brands Yet</h3>
          <p className="text-gray-400 mb-6">Create a brand first to connect Instagram</p>
          <Link
            href="/dashboard/brands"
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2"
          >
            Create Brand
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedBrands).map(([orgName, orgBrands]) => (
            <div key={orgName} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                {orgName === 'Personal' ? '👤' : '🏢'} {orgName}
                <span className="text-sm font-normal text-gray-500">
                  ({orgBrands.filter(b => b.instagram_connected).length}/{orgBrands.length} connected)
                </span>
              </h2>

              <div className="space-y-3">
                {orgBrands.map((brand) => (
                  <div
                    key={brand.id}
                    className="bg-black border border-white/10 rounded-lg p-4 hover:border-purple-500/30 transition"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-lg font-bold flex-shrink-0">
                        {brand.name.substring(0, 2).toUpperCase()}
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium">{brand.name}</h3>
                        {brand.description && (
                          <p className="text-sm text-gray-400 truncate">{brand.description}</p>
                        )}
                      </div>

                      {brand.instagram_connected ? (
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="flex items-center gap-2 text-green-400 text-sm font-medium">
                              <CheckCircle className="w-4 h-4" />
                              Connected
                            </div>
                            {brand.instagram_username && (
                              <p className="text-xs text-gray-500">@{brand.instagram_username}</p>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Link
                              href={`/dashboard/brands/${brand.slug}/instagram`}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm transition"
                            >
                              Manage
                            </Link>
                            <button
                              onClick={() => handleDisconnect(brand.id)}
                              className="bg-red-600/20 hover:bg-red-600/30 text-red-400 px-3 py-2 rounded-lg text-sm transition border border-red-600/30"
                            >
                              Disconnect
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <XCircle className="w-4 h-4" />
                            Not Connected
                          </div>
                          <button
                            onClick={() => handleConnect(brand.id)}
                            disabled={brand.isConnecting}
                            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition flex items-center gap-2"
                          >
                            {brand.isConnecting ? (
                              <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                Connecting...
                              </>
                            ) : (
                              <>
                                <Instagram className="w-4 h-4" />
                                Connect
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 mt-6">
        <h3 className="text-lg font-semibold text-white mb-4">Requirements</h3>
        <ul className="space-y-2 text-sm text-gray-400">
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            <span>Your Instagram account must be a <strong className="text-white">Business</strong> or <strong className="text-white">Creator</strong> account</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            <span>Instagram must be linked to a <strong className="text-white">Facebook Page</strong></span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            <span>You need admin access to the Facebook Page</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
