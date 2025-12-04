"use client";

import { useState, useEffect, useCallback } from 'react';
import { twitterAPI, QueuedTweet, TwitterConfig, CreateTweetData } from '@/lib/api/twitter';
import { toast } from 'sonner';

export function useTwitterConfig(brandId?: number) {
  const [config, setConfig] = useState<TwitterConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchConfig = useCallback(async () => {
    if (!brandId) {
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      const data = await twitterAPI.getConfig(brandId);
      setConfig(data);
    } catch (error: any) {
      console.error('Failed to fetch Twitter config:', error);
      
      if (error.message.includes('Authentication required')) {
        toast.error('Please login again to access Twitter features');
      }
      
      setConfig(null);
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  const saveConfig = useCallback(async (data: Partial<TwitterConfig>) => {
    if (!brandId) {
      toast.error('Brand ID is required to save Twitter config');
      return;
    }

    try {
      setIsSaving(true);
      const updatedConfig = await twitterAPI.saveConfig(brandId, data);
      setConfig(updatedConfig);
      toast.success('Twitter configuration saved successfully');
      return updatedConfig;
    } catch (error: any) {
      console.error('Failed to save Twitter config:', error);
      toast.error(error.message || 'Failed to save Twitter configuration');
      throw error;
    } finally {
      setIsSaving(false);
    }
  }, [brandId]);

  const testConnection = useCallback(async () => {
    if (!brandId) {
      toast.error('Brand ID is required to test connection');
      return;
    }

    try {
      const result = await twitterAPI.testConnection(brandId);
      
      if (result.success) {
        toast.success(`Connected as @${result.username}`);
      } else {
        toast.error(result.error || 'Connection test failed');
      }
      
      return result;
    } catch (error: any) {
      console.error('Failed to test Twitter connection:', error);
      toast.error(error.message || 'Failed to test connection');
    }
  }, [brandId]);

  const disconnect = useCallback(async () => {
    if (!brandId) {
      toast.error('Brand ID is required to disconnect Twitter');
      return;
    }

    try {
      await twitterAPI.disconnect(brandId);
      toast.success('Twitter disconnected successfully');
      setConfig(null);
    } catch (error: any) {
      console.error('Failed to disconnect Twitter:', error);
      toast.error(error.message || 'Failed to disconnect Twitter');
    }
  }, [brandId]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return {
    config,
    isLoading,
    isSaving,
    saveConfig,
    testConnection,
    disconnect,
    refetch: fetchConfig,
  };
}

export function useTwitterQueue(brandId?: number) {
  const [tweets, setTweets] = useState<QueuedTweet[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    total_queued: 0,
    total_scheduled: 0,
    total_drafts: 0,
    total_posted: 0,
  });

  const fetchQueue = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await twitterAPI.getQueue(brandId);
      setTweets(data.tweets);
      setStats(data.stats);
    } catch (error: any) {
      console.error('Failed to fetch Twitter queue:', error);
      toast.error('Failed to fetch Twitter queue');
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  const createTweet = useCallback(async (data: CreateTweetData & { brand_id: number }) => {
    try {
      const newTweet = await twitterAPI.createQueuedTweet(data);
      setTweets(prev => [newTweet, ...prev]);
      toast.success('Tweet created successfully');
      
      // Update stats
      setStats(prev => ({
        ...prev,
        total_drafts: prev.total_drafts + (newTweet.status === 'draft' ? 1 : 0),
        total_scheduled: prev.total_scheduled + (newTweet.status === 'scheduled' ? 1 : 0),
      }));
      
      return newTweet;
    } catch (error: any) {
      console.error('Failed to create tweet:', error);
      toast.error(error.message || 'Failed to create tweet');
      throw error;
    }
  }, []);

  const updateTweet = useCallback(async (tweetId: number, data: Partial<CreateTweetData>) => {
    try {
      const updatedTweet = await twitterAPI.updateQueuedTweet(tweetId, data);
      setTweets(prev => prev.map(tweet => tweet.id === tweetId ? updatedTweet : tweet));
      toast.success('Tweet updated successfully');
      return updatedTweet;
    } catch (error: any) {
      console.error('Failed to update tweet:', error);
      toast.error(error.message || 'Failed to update tweet');
      throw error;
    }
  }, []);

  const deleteTweet = useCallback(async (tweetId: number) => {
    try {
      await twitterAPI.deleteQueuedTweet(tweetId);
      setTweets(prev => prev.filter(tweet => tweet.id !== tweetId));
      toast.success('Tweet deleted successfully');
      
      // Refetch to update stats
      await fetchQueue();
    } catch (error: any) {
      console.error('Failed to delete tweet:', error);
      toast.error(error.message || 'Failed to delete tweet');
    }
  }, [fetchQueue]);

  const postNow = useCallback(async (tweetId: number) => {
    try {
      const result = await twitterAPI.postTweetNow(tweetId);
      
      if (result.success) {
        toast.success('Tweet posted successfully');
        // Refresh queue to get updated status
        await fetchQueue();
      } else {
        toast.error(result.error || 'Failed to post tweet');
      }
      
      return result;
    } catch (error: any) {
      console.error('Failed to post tweet:', error);
      toast.error(error.message || 'Failed to post tweet');
    }
  }, [fetchQueue]);

  const generateAITweets = useCallback(async (
    brandId: number,
    params: {
      prompt: string;
      count?: number;
      tone?: 'professional' | 'casual' | 'funny' | 'inspirational';
    }
  ) => {
    try {
      const result = await twitterAPI.generateAITweets(brandId, params);
      
      if (result.success) {
        toast.success(`Generated ${result.count} tweets successfully`);
        // Refresh queue to show new tweets
        await fetchQueue();
      } else {
        toast.error(result.error || 'Failed to generate tweets');
      }
      
      return result;
    } catch (error: any) {
      console.error('Failed to generate AI tweets:', error);
      toast.error(error.message || 'Failed to generate AI tweets');
      throw error;
    }
  }, [fetchQueue]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  return {
    tweets,
    isLoading,
    stats,
    createTweet,
    updateTweet,
    deleteTweet,
    postNow,
    generateAITweets,
    refetch: fetchQueue,
  };
}
