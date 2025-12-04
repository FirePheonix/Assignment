"use client";

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { CheckCircle, AlertCircle, Instagram } from 'lucide-react';

export default function InstagramOAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const success = searchParams.get('success');
    const error = searchParams.get('error');

    // Check if this is a popup window
    const isPopup = window.opener && window.parent !== window;

    if (isPopup) {
      // Handle popup flow - send message to parent window
      if (success === 'true') {
        window.opener?.postMessage(
          { type: 'INSTAGRAM_OAUTH_SUCCESS' },
          window.location.origin
        );
        window.close();
        return;
      } else if (error) {
        window.opener?.postMessage(
          { 
            type: 'INSTAGRAM_OAUTH_ERROR',
            error: error 
          },
          window.location.origin
        );
        window.close();
        return;
      }
    }

    // Handle direct redirect flow
    if (success === 'true') {
      toast.success('Instagram account connected successfully!');
      
      // Add a small delay to ensure backend has processed the OAuth
      setTimeout(() => {
        // Redirect back to brands page or specific brand page
        const brandId = localStorage.getItem('instagram_connecting_brand_id');
        if (brandId) {
          localStorage.removeItem('instagram_connecting_brand_id');
          // Get brand slug from localStorage or redirect to brands list
          const brandSlug = localStorage.getItem('instagram_connecting_brand_slug');
          if (brandSlug) {
            localStorage.removeItem('instagram_connecting_brand_slug');
            // Add a refresh flag to force re-fetch of Instagram status
            const targetUrl = `/dashboard/brands/${brandSlug}/instagram?refresh=true`;
            router.push(targetUrl);
          } else {
            router.push('/dashboard/brands');
          }
        } else {
          router.push('/dashboard/brands');
        }
      }, 1000); // 1 second delay to ensure backend processing is complete
    } else if (error) {
      let errorMessage = 'Failed to connect Instagram account';
      
      switch (error) {
        case 'missing_params':
          errorMessage = 'Missing required parameters from Instagram';
          break;
        case 'invalid_state':
          errorMessage = 'Invalid authentication state. Please try again.';
          break;
        case 'token_exchange_failed':
          errorMessage = 'Failed to exchange authorization code for token';
          break;
        case 'no_pages':
          errorMessage = 'No Facebook pages found. Make sure you have a Facebook page connected.';
          break;
        case 'no_instagram_account':
          errorMessage = 'No Instagram Business Account linked to your Facebook page';
          break;
        case 'api_request_failed':
          errorMessage = 'API request failed. Please try again.';
          break;
        case 'brand_not_found':
          errorMessage = 'Brand not found. Please contact support.';
          break;
        default:
          errorMessage = `Connection failed: ${error}`;
      }
      
      toast.error(errorMessage);
      
      // Redirect back with error state
      const brandId = localStorage.getItem('instagram_connecting_brand_id');
      if (brandId) {
        localStorage.removeItem('instagram_connecting_brand_id');
        const brandSlug = localStorage.getItem('instagram_connecting_brand_slug');
        if (brandSlug) {
          localStorage.removeItem('instagram_connecting_brand_slug');
          router.push(`/dashboard/brands/${brandSlug}/instagram`);
        } else {
          router.push('/dashboard/brands');
        }
      } else {
        router.push('/dashboard/brands');
      }
    } else {
      // No success or error parameter, redirect to brands
      router.push('/dashboard/brands');
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-8">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />
      
      <div className="relative z-10 text-center">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
          <Instagram className="w-8 h-8" />
        </div>
        
        <h1 className="text-2xl font-bold mb-4">Processing Instagram Connection...</h1>
        
        <div className="flex items-center justify-center gap-2 text-gray-400">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500"></div>
          <span>Please wait while we complete the connection</span>
        </div>
      </div>
    </div>
  );
}