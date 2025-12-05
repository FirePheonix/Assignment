"use client";

import { Search, User, MessageSquare, Loader2, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { chatApi } from "@/lib/chat-api";
import { toast } from "sonner";

export default function NewConversationPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [searching, setSearching] = useState(false);

  const handleStartConversation = async () => {
    if (!email.trim()) {
      toast.error('Please enter an email address');
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    try {
      setSearching(true);

      const token = localStorage.getItem('auth_token');
      const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

      const response = await fetch(`${DJANGO_BACKEND}/chat/conversation/start/email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start conversation');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          data.created 
            ? 'New conversation started!' 
            : 'Opened existing conversation'
        );
        router.push(`/dashboard/chat?conversation=${data.conversation_id}`);
      } else {
        throw new Error(data.error || 'Failed to start conversation');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to start conversation');
    } finally {
      setSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !searching) {
      handleStartConversation();
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Messages
        </button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">New Conversation</h1>
          <p className="text-gray-400">Start a conversation with another user</p>
        </div>

        {/* Search Card */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-8">
          <div className="mb-6">
            <label className="block text-sm font-medium text-white mb-2">
              User Email Address
            </label>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="user@example.com"
                disabled={searching}
                className="w-full pl-12 pr-4 py-4 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
              />
            </div>
            <p className="text-sm text-gray-400 mt-2">
              Enter the email address of the user you want to message
            </p>
          </div>

          <button
            onClick={handleStartConversation}
            disabled={searching || !email.trim()}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-4 rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {searching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <MessageSquare className="w-5 h-5" />
                Start Conversation
              </>
            )}
          </button>
        </div>

        {/* Info Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <MessageSquare className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">Direct Messaging</h3>
                <p className="text-sm text-gray-400">
                  Send private messages to other users on the platform
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-pink-500/20 rounded-lg">
                <User className="w-5 h-5 text-pink-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">Find Users</h3>
                <p className="text-sm text-gray-400">
                  Search by email to connect with creators and brands
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
