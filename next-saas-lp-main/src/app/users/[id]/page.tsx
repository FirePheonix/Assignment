"use client";

import { User, Mail, Instagram, MessageSquare, Loader2, ArrowLeft } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { userApi, type UserProfile } from "@/lib/user-api";
import { getCurrentUser } from "@/lib/auth";
import { chatApi } from "@/lib/chat-api";
import { toast } from "sonner";

export default function UserProfilePage() {
  const router = useRouter();
  const params = useParams();
  const userId = params.id as string;
  
  const [user, setUser] = useState<UserProfile | null>(null);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingChat, setStartingChat] = useState(false);

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load current user
      const current = await getCurrentUser();
      if (current) {
        const currentProfile = await userApi.getCurrentProfile();
        setCurrentUser(currentProfile);
      }

      // Load the specific user's profile by ID
      const profile = await userApi.getProfile(parseInt(userId));
      console.log('Loaded user profile:', profile);
      console.log('Profile picture URL:', profile.profile_picture);
      setUser(profile);
    } catch (error) {
      console.error('Error loading user profile:', error);
      toast.error('Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async () => {
    if (!user || startingChat) return;

    try {
      setStartingChat(true);
      
      const result = await chatApi.startConversationWithUser(user.id);
      
      if (result.created) {
        toast.success('New conversation started!');
      }
      
      // Redirect to chat page with conversation
      router.push(`/dashboard/chat?conversation=${result.conversation.id}`);
    } catch (error) {
      console.error('Error starting chat:', error);
      toast.error('Failed to start conversation');
    } finally {
      setStartingChat(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto" />
          <p className="mt-4 text-gray-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-center">
          <User className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-xl text-gray-400">User not found</p>
          <button
            onClick={() => router.back()}
            className="mt-4 text-purple-400 hover:text-purple-300"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  const isOwnProfile = currentUser?.id === user.id;

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        {/* Profile Header */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-8">
          <div className="flex flex-col md:flex-row items-start gap-6">
            {/* Avatar */}
            <div className="flex-shrink-0">
              {user.profile_picture && user.profile_picture.trim() !== '' ? (
                <img
                  src={user.profile_picture}
                  alt={user.username}
                  className="w-32 h-32 rounded-full object-cover"
                  onError={(e) => {
                    console.error('Failed to load profile image:', user.profile_picture);
                    e.currentTarget.style.display = 'none';
                    if (e.currentTarget.nextElementSibling) {
                      (e.currentTarget.nextElementSibling as HTMLElement).style.display = 'flex';
                    }
                  }}
                />
              ) : null}
              <div 
                className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-4xl font-bold text-white"
                style={{ display: user.profile_picture && user.profile_picture.trim() !== '' ? 'none' : 'flex' }}
              >
                {user.first_name?.[0] || user.username[0]}
              </div>
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">
                    {user.first_name && user.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user.username}
                  </h1>
                  <p className="text-gray-400">@{user.username}</p>
                </div>

                {!isOwnProfile && currentUser && (
                  <button
                    onClick={handleStartChat}
                    disabled={startingChat}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition disabled:opacity-50"
                  >
                    {startingChat ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <MessageSquare className="w-5 h-5" />
                        Send Message
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Stats */}
              <div className="flex gap-6 mb-6">
                {user.impressions_count !== undefined && (
                  <div>
                    <p className="text-2xl font-bold text-white">
                      {user.impressions_count.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-400">Profile Views</p>
                  </div>
                )}
                {user.age && (
                  <div>
                    <p className="text-2xl font-bold text-white">{user.age}</p>
                    <p className="text-sm text-gray-400">Years Old</p>
                  </div>
                )}
              </div>

              {/* Bio */}
              {user.bio && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">About</h3>
                  <p className="text-white whitespace-pre-wrap">{user.bio}</p>
                </div>
              )}

              {/* Contact Info */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-gray-400">
                  <Mail className="w-4 h-4" />
                  <span>{user.email}</span>
                </div>
                {user.instagram_handle && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <Instagram className="w-4 h-4" />
                    <a
                      href={`https://instagram.com/${user.instagram_handle.replace('@', '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-purple-400 transition"
                    >
                      {user.instagram_handle}
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Additional Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">Activity</h3>
            <div className="space-y-3 text-gray-400">
              <p className="text-sm">
                Member since{' '}
                {user.created_at
                  ? new Date(user.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                    })
                  : 'N/A'}
              </p>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">Skills & Interests</h3>
            <div className="flex flex-wrap gap-2">
              <span className="bg-purple-500/20 text-purple-400 px-3 py-1 rounded-full text-sm">
                Content Creator
              </span>
              <span className="bg-pink-500/20 text-pink-400 px-3 py-1 rounded-full text-sm">
                Social Media
              </span>
              <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-sm">
                Marketing
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
