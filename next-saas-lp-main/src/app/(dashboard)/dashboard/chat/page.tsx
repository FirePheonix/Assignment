"use client";

import { MessageSquare, Search, Send, MoreVertical, Paperclip, UserPlus, Loader2 } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { chatApi, type Conversation, type Message } from "@/lib/chat-api";
import { getCurrentUser } from "@/lib/auth";
import { toast } from "sonner";
import { useRouter, useSearchParams } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [message, setMessage] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // -----------------------------
  // URL PARAM CHECK
  // -----------------------------
  useEffect(() => {
    const convId = searchParams.get("conversation");
    if (convId) {
      setSelectedConversation(parseInt(convId));
    }
  }, [searchParams]);

  // -----------------------------
  // LOAD USER + CONVERSATIONS
  // -----------------------------
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const user = await getCurrentUser();
      if (user) setCurrentUserId(user.id);

      const data = await chatApi.getConversations();
      setConversations(data.chats);

      if (data.chats.length > 0 && !selectedConversation) {
        setSelectedConversation(data.chats[0].id);
      }
    } catch (e) {
      toast.error("Failed to load conversations");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------
  // LOAD MESSAGES FOR SELECTED
  // -----------------------------
  useEffect(() => {
    if (!selectedConversation) return;

    loadMessages(selectedConversation);
    setupWebSocket(selectedConversation);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [selectedConversation]);

  const loadMessages = async (conversationId: number) => {
    try {
      const conversation = await chatApi.getConversation(conversationId);
      setMessages(conversation.messages || []);
    } catch (e) {
      toast.error("Failed to load messages");
    }
  };

  // -----------------------------
  // WEBSOCKET SETUP
  // -----------------------------
  const setupWebSocket = (conversationId: number) => {
    const ws = chatApi.createWebSocket(conversationId);
    if (!ws) return;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "chat_message") {
        const newMessage: Message = {
          id: data.message_id,
          sender: { id: data.user_id, username: data.username },
          content: data.message,
          timestamp: data.timestamp,
          is_read: false,
          image: data.image_url,
        };

        setMessages((prev) => [...prev, newMessage]);
        loadData();
      }
    };

    wsRef.current = ws;
  };

  // -----------------------------
  // SEND MESSAGE
  // -----------------------------
  const handleSendMessage = async () => {
    if (!message.trim() || !selectedConversation || sending) return;

    const msg = message.trim();
    setMessage("");
    setSending(true);

    try {
      await chatApi.sendMessage(selectedConversation, msg);
    } catch (e) {
      toast.error("Failed to send");
      setMessage(msg);
    } finally {
      setSending(false);
    }
  };

  // -----------------------------
  // UTILS
  // -----------------------------
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getOtherParticipant = (conv: Conversation) => {
    if (!currentUserId) return conv.participant2;
    return conv.participant1.id === currentUserId ? conv.participant2 : conv.participant1;
  };

  const getConversationName = (conv: Conversation) => {
    if (conv.brand) return conv.brand.name;
    const other = getOtherParticipant(conv);
    return other.first_name && other.last_name
      ? `${other.first_name} ${other.last_name}`
      : other.username;
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = diff / 60000;
    const hours = diff / 3600000;
    const days = diff / 86400000;

    if (mins < 1) return "Just now";
    if (mins < 60) return `${Math.floor(mins)}m ago`;
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    if (days < 2) return "Yesterday";
    return date.toLocaleDateString();
  };

  const selectedConvObj = conversations.find((c) => c.id === selectedConversation);

  // -----------------------------
  // LOADING UI
  // -----------------------------
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  // -----------------------------
  // MAIN UI
  // -----------------------------
  return (
    <div className="h-screen bg-[#0a0a0a] flex overflow-hidden">
      {/* SIDEBAR */}
      <div className="w-80 bg-[#121212] flex flex-col">
        <div className="p-4 border-b border-white/5">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg text-white font-semibold">Messages</h2>
            <button
              onClick={() => router.push("/dashboard/chat/new")}
              className="p-1.5 hover:bg-white/10 rounded-lg"
            >
              <UserPlus className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-4 h-4" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search"
              className="w-full bg-[#1a1a1a] text-white text-sm pl-9 pr-3 py-2 rounded-lg outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations
            .filter((c) =>
              getConversationName(c).toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((conv) => {
              const other = getOtherParticipant(conv);
              const name = getConversationName(conv);
              const selected = conv.id === selectedConversation;

              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv.id)}
                  className={`p-3 border-b border-white/5 cursor-pointer hover:bg-white/5 ${
                    selected ? "bg-white/5" : ""
                  }`}
                >
                  <div className="flex gap-3 items-center">
                    {other.profile_picture ? (
                      <img src={other.profile_picture} className="w-12 h-12 rounded-full" />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex justify-center items-center text-white">
                        {name.substring(0, 2).toUpperCase()}
                      </div>
                    )}

                    <div className="flex-1">
                      <p className="text-white text-sm font-medium truncate">{name}</p>
                      <p className="text-xs text-gray-400 truncate">
                        {conv.last_message?.content || "No messages yet"}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* CHAT AREA */}
      {selectedConvObj ? (
        <div className="flex-1 flex flex-col bg-[#0a0a0a]">
          {/* HEADER */}
          <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-[#121212]">
            <div className="flex items-center gap-3">
              {getOtherParticipant(selectedConvObj).profile_picture ? (
                <img
                  src={getOtherParticipant(selectedConvObj).profile_picture}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex justify-center items-center text-white">
                  {getConversationName(selectedConvObj).substring(0, 2).toUpperCase()}
                </div>
              )}

              <div>
                <h3 className="text-white text-sm font-semibold">
                  {getConversationName(selectedConvObj)}
                </h3>
                <p className="text-xs text-gray-400">
                  {selectedConvObj.brand ? "Brand" : "Creator"}
                </p>
              </div>
            </div>

            <button className="p-2 hover:bg-white/10 rounded-lg transition">
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {/* MESSAGES */}
          <div className="flex-1 overflow-y-auto px-6 space-y-4 py-4">
            {messages.map((msg, i) => {
              const isMe = msg.sender.id === currentUserId;

              return (
                <div key={msg.id} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-md px-4 py-2 rounded-2xl ${
                      isMe ? "bg-blue-600 text-white" : "bg-[#1f1f1f] text-white"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef}></div>
          </div>

          {/* INPUT */}
          <div className="px-6 py-4 border-t border-white/5 bg-[#121212]">
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-white/10 rounded-lg">
                <Paperclip className="w-5 h-5 text-gray-400" />
              </button>

              <div className="flex-1 bg-[#1a1a1a] rounded-full px-4 py-2 flex items-center">
                <input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Write a message..."
                  className="flex-1 bg-transparent text-white outline-none"
                />

                <button
                  disabled={!message.trim() || sending}
                  onClick={handleSendMessage}
                  className="ml-2 disabled:opacity-50"
                >
                  {sending ? (
                    <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                  ) : (
                    <Send
                      className={`w-5 h-5 ${
                        message.trim() ? "text-blue-500" : "text-gray-500"
                      }`}
                    />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex justify-center items-center text-gray-400">
          <div className="text-center">
            <MessageSquare className="w-20 h-20 mx-auto mb-4 opacity-20" />
            <h3 className="text-white text-lg font-semibold">Select a conversation</h3>
            <p className="text-gray-500 text-sm">Choose a conversation from the sidebar</p>
          </div>
        </div>
      )}
    </div>
  );
}
