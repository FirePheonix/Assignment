"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Instagram,
  ArrowLeft,
  Plus,
  Calendar,
  Edit,
  Trash2,
  Play,
  AlertCircle,
  CheckCircle,
  ExternalLink,
} from "lucide-react";

import { useInstagramAuth, useInstagramPosts } from "@/hooks/use-instagram";
import { brandsAPI, type Brand as APIBrand } from "@/lib/api/brands";
import { ImageGallery, ImageUploadBox } from "@/components/ImageGallery";
import { CreatePostData } from "@/lib/api/instagram";
import { toast } from "sonner";

// -----------------------------
// Local types (adapt if your hooks/APIs differ)
// -----------------------------
type Nullable<T> = T | null;

interface Brand extends APIBrand {
  // reuse fields from APIBrand and add any local-only fields if needed
}

interface Account {
  connected: boolean;
  instagram_username?: string;
  // ...other fields from your hook if present
}

interface Post {
  id: string | number;
  image: string;
  content?: string | null;
  caption?: string | null;
  scheduled_for?: string | null;
  scheduled_time?: string | null;
  status?: string;
  instagram_url?: string | null;
  // other fields from the API...
}

interface CreatePostFormData {
  caption: string;
  image: string;
  scheduled_time: string;
}

// -----------------------------
// Component
// -----------------------------
export default function BrandInstagramPage() {
  const params = useParams();
  const router = useRouter();
  const brandSlug = (params as any)?.slug as string | undefined;

  const [brand, setBrand] = useState<Nullable<Brand>>(null);
  const [loading, setLoading] = useState(true);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showImageGallery, setShowImageGallery] = useState(false);

  const [editingPost, setEditingPost] = useState<Nullable<Post>>(null);

  const [formData, setFormData] = useState<CreatePostFormData>({
    caption: "",
    image: "",
    scheduled_time: "",
  });

  const modalRef = useRef<HTMLDivElement | null>(null);

  // ---------------------------------------------------------
  // Load brand data
  // ---------------------------------------------------------
  useEffect(() => {
    let mounted = true;

    const loadBrand = async () => {
      setLoading(true);
      try {
        const brands = await brandsAPI.getBrands();
        const foundBrand = brands.find((b: Brand) => b.slug === brandSlug);

        if (!foundBrand) {
          // If brand slug invalid, redirect back
          router.push("/dashboard/brands");
          return;
        }

        if (mounted) setBrand(foundBrand);
      } catch (error) {
        console.error("Failed to load brand:", error);
        toast.error("Failed to load brand");
        router.push("/dashboard/brands");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    if (brandSlug) loadBrand();
    else setLoading(false);

    return () => {
      mounted = false;
    };
  }, [brandSlug, router]);

  // ---------------------------------------------------------
  // Instagram hooks
  // (Assumes these hooks accept brand id and return the shapes used below)
  // ---------------------------------------------------------
  const { account, isConnecting, connect, disconnect, refetch } = useInstagramAuth(
    brand?.id ?? undefined
  ) as {
    account: Nullable<Account>;
    isConnecting: boolean;
    connect: () => Promise<void>;
    disconnect: () => Promise<void>;
    refetch: () => void;
  };

  const {
    posts = [],
    isLoading: postsLoading,
    createPost,
    updatePost,
    deletePost,
    postNow,
    refetch: refetchPosts,
  } = (useInstagramPosts(brand?.id) as unknown) as {
    posts: Post[];
    isLoading: boolean;
    createPost: (payload: CreatePostData) => Promise<void>;
    updatePost: (id: string | number, payload: Partial<CreatePostData>) => Promise<void>;
    deletePost: (id: string | number) => Promise<void>;
    postNow: (id: string | number) => Promise<void>;
    refetch: () => void;
  };

  // ---------------------------------------------------------
  // OAuth callback refresh (if ?refresh=true in URL)
  // ---------------------------------------------------------
  useEffect(() => {
    if (typeof window === "undefined") return;

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("refresh") === "true") {
      const newUrl = window.location.pathname;
      window.history.replaceState({}, "", newUrl);

      // Small delay to give backend a moment (mirrors original logic)
      setTimeout(() => {
        try {
          refetch?.();
          refetchPosts?.();
        } catch (err) {
          console.warn("Error refetching after refresh param:", err);
        }
      }, 400);
    }
  }, [refetch, refetchPosts]);

  // ---------------------------------------------------------
  // FORM HANDLERS
  // ---------------------------------------------------------
  const resetForm = useCallback(() => {
    setFormData({ caption: "", image: "", scheduled_time: "" });
    setEditingPost(null);
    setShowCreateForm(false);
    setShowImageGallery(false);
  }, []);

  const handleCreatePost = useCallback(async () => {
    if (!formData.caption.trim()) {
      toast.error("Caption required");
      return;
    }
    if (!formData.image) {
      toast.error("Select an image");
      return;
    }
    if (!brand?.id) {
      toast.error("Brand not selected");
      return;
    }

    try {
      const payload: CreatePostData = {
        caption: formData.caption,
        imageUrl: formData.image,
        brand_id: brand.id,
        scheduled_time: formData.scheduled_time || undefined,
      };

      await createPost(payload);
      toast.success("Post created");
      refetchPosts?.();
      resetForm();
    } catch (err) {
      console.error("Create post failed:", err);
      toast.error("Failed to create post");
    }
  }, [formData, brand?.id, createPost, refetchPosts, resetForm]);

  const handleUpdatePost = useCallback(async () => {
    if (!editingPost) return;
    try {
      await updatePost(editingPost.id, {
        caption: formData.caption,
        imageUrl: formData.image,
        scheduled_time: formData.scheduled_time || undefined,
      });
      toast.success("Post updated");
      refetchPosts?.();
      resetForm();
    } catch (err) {
      console.error("Update post failed:", err);
      toast.error("Failed to update post");
    }
  }, [editingPost, formData, updatePost, refetchPosts, resetForm]);

  const handleDeletePost = useCallback(
    async (id: string | number) => {
      try {
        await deletePost(id);
        toast.success("Post deleted");
        refetchPosts?.();
      } catch (err) {
        console.error("Delete failed:", err);
        toast.error("Failed to delete post");
      }
    },
    [deletePost, refetchPosts]
  );

  const handlePostNow = useCallback(
    async (id: string | number) => {
      try {
        await postNow(id);
        toast.success("Posted to Instagram");
        refetchPosts?.();
      } catch (err) {
        console.error("Post now failed:", err);
        toast.error("Failed to post now");
      }
    },
    [postNow, refetchPosts]
  );

  const startEdit = (post: Post) => {
    setEditingPost(post);
    setFormData({
      caption: post.content ?? post.caption ?? "",
      image: post.image ?? "",
      scheduled_time: post.scheduled_for ?? post.scheduled_time ?? "",
    });
    setShowCreateForm(true);
    setShowImageGallery(false);
  };

  // ---------------------------------------------------------
  // CLICK OUTSIDE TO CLOSE
  // ---------------------------------------------------------
  useEffect(() => {
    if (!showCreateForm) return;

    const handleOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        resetForm();
      }
    };

    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [showCreateForm, resetForm]);

  // ---------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------
  const formatDate = (time?: string | null) => {
    if (!time) return "";
    const d = new Date(time);
    if (Number.isNaN(d.getTime())) return time; // fallback to raw string
    return d.toLocaleString();
  };

  const statusColor: Record<string, string> = {
    posted: "text-green-400 bg-green-500/20",
    approved: "text-blue-400 bg-blue-500/20",
    scheduled: "text-blue-400 bg-blue-500/20",
    draft: "text-gray-400 bg-gray-500/20",
    failed: "text-red-400 bg-red-500/20",
    default: "text-gray-400 bg-gray-500/20",
  };

  // ---------------------------------------------------------
  // Render guards
  // ---------------------------------------------------------
  if (loading)
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="animate-spin h-8 w-8 rounded-full border-b-2 border-purple-500"></div>
      </div>
    );

  if (!brand)
    return (
      <div className="min-h-screen bg-black text-white p-8">
        <div className="max-w-xl mx-auto text-center">
          <h1 className="text-2xl font-bold mb-4">Brand Not Found</h1>
          <Link
            href="/dashboard/brands"
            className="px-6 py-3 bg-purple-600 rounded-lg flex items-center gap-2 mx-auto w-fit"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
        </div>
      </div>
    );

  // ============================================================
  // MAIN UI
  // ============================================================
  return (
    <div className="min-h-screen bg-black text-white p-8 relative">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Link href="/dashboard/brands" className="p-2 hover:bg-white/10 rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center rounded-lg font-bold">
            {brand.name.substring(0, 2)}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{brand.name} – Instagram</h1>
            <p className="text-gray-400">
              {brand.organization_name && brand.organization_name + " • "}
              Instagram Management
            </p>
          </div>
        </div>

        {/* Connect Box */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between">
          {account?.connected ? (
            <>
              <div className="flex items-center gap-3">
                <div className="bg-green-500/20 p-2 rounded-lg">
                  <CheckCircle className="text-green-400 w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium">Instagram Connected</p>
                  <p className="text-gray-400 text-sm">@{account.instagram_username}</p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg"
                  onClick={() => setShowCreateForm(true)}
                >
                  <Plus className="w-4 h-4 inline-block" /> Create
                </button>

                <button
                  onClick={() =>
                    disconnect().catch((err) => {
                      console.error("Disconnect error:", err);
                      toast.error("Failed to disconnect");
                    })
                  }
                  className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 border border-red-600/30"
                >
                  Disconnect
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium">Instagram Not Connected</p>
                  <p className="text-gray-400 text-sm">Connect to enable posting</p>
                </div>
              </div>

              <button
                disabled={isConnecting}
                onClick={() => connect().catch((err) => {
                  console.error("Connect err:", err);
                  toast.error("Failed to connect");
                })}
                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg disabled:opacity-60"
              >
                {isConnecting ? "Connecting..." : "Connect"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* POSTS */}
      {account?.connected && (
        <div className="space-y-6 mt-10">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Posts</h2>
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-4 py-2 rounded-lg bg-purple-600"
            >
              <Plus className="w-4 h-4 inline-block" /> New Post
            </button>
          </div>

          {/* Loading Skeleton */}
          {postsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-70">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-60 bg-white/5 animate-pulse rounded-lg"></div>
              ))}
            </div>
          ) : posts.length ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {posts.map((post) => (
                <div
                  key={post.id}
                  className="bg-white/5 border border-white/10 rounded-lg overflow-hidden"
                >
                  <div className="aspect-square relative">
                    <img src={post.image} alt="post image" className="w-full h-full object-cover" />

                    <span
                      className={`absolute top-2 right-2 px-2 py-1 text-xs rounded-full ${
                        statusColor[post.status ?? ""] || statusColor.default
                      }`}
                    >
                      {post.status ?? "unknown"}
                    </span>
                  </div>

                  <div className="p-4 space-y-3">
                    <p className="text-sm text-gray-300 line-clamp-3">
                      {post.content ?? post.caption ?? ""}
                    </p>

                    {(post.scheduled_for || post.scheduled_time) && (
                      <p className="text-xs text-gray-400 flex gap-2">
                        <Calendar className="w-3 h-3" />
                        {formatDate(post.scheduled_for ?? post.scheduled_time)}
                      </p>
                    )}

                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(post)}
                        className="flex-1 bg-white/5 hover:bg-white/10 px-3 py-2 rounded text-xs"
                      >
                        <Edit className="w-3 h-3 inline-block" /> Edit
                      </button>

                      {(post.status === "approved" || post.status === "scheduled") && (
                        <button
                          onClick={() => handlePostNow(post.id)}
                          className="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-400 px-3 py-2 rounded text-xs"
                        >
                          <Play className="w-3 h-3 inline-block" /> Post Now
                        </button>
                      )}

                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="bg-red-500/20 hover:bg-red-500/30 text-red-400 px-3 py-2 rounded text-xs"
                      >
                        <Trash2 className="w-3 h-3 inline-block" />
                      </button>
                    </div>

                    {post.instagram_url && (
                      <a href={post.instagram_url} target="_blank" rel="noreferrer" className="text-xs text-purple-400 flex items-center gap-1">
                        <ExternalLink className="w-3 h-3" /> View on Instagram
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-16 bg-white/5 rounded-lg border border-white/10 text-center">
              <Instagram className="w-10 h-10 mx-auto text-gray-500 mb-4" />
              <h3 className="text-lg font-bold">No Posts Yet</h3>
              <p className="text-gray-400 mt-2">Create your first post!</p>

              <button
                onClick={() => setShowCreateForm(true)}
                className="mt-5 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg"
              >
                Create Post
              </button>
            </div>
          )}
        </div>
      )}

      {/* ============================================================
           CREATE / EDIT MODAL
      ============================================================ */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
          <div ref={modalRef} className="w-full max-w-lg bg-gray-900 border border-white/10 rounded-2xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">{editingPost ? "Edit Post" : "Create Post"}</h2>

              <button onClick={resetForm} className="text-gray-400 hover:text-white">✕</button>
            </div>

            <div className="space-y-5">
              {/* IMAGE */}
              <div>
                <label className="block text-sm font-medium mb-2">Image</label>

                {formData.image ? (
                  <div className="relative">
                    <img src={formData.image} className="rounded-lg border border-white/10 w-full aspect-square object-cover" alt="selected" />

                    <button
                      onClick={() => setFormData((s) => ({ ...s, image: "" }))}
                      className="absolute top-2 right-2 bg-red-600 p-2 rounded-full"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <ImageUploadBox
                      currentImage=""
                      onImageUpload={(url: string) => setFormData((s) => ({ ...s, image: url }))}
                      className="aspect-square"
                    />

                    <button
                      className="w-full py-2 rounded-lg bg-white/5 border border-white/10 text-sm"
                      onClick={() => setShowImageGallery((v) => !v)}
                      type="button"
                    >
                      {showImageGallery ? "Hide Gallery" : "Choose from Gallery"}
                    </button>

                    {showImageGallery && (
                      <div className="border border-white/10 rounded-lg p-3">
                        <ImageGallery
                          selectedImage={formData.image}
                          onImageSelect={(url: string) => {
                            setFormData((s) => ({ ...s, image: url }));
                            setShowImageGallery(false);
                          }}
                          showUpload={false}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* CAPTION */}
              <div>
                <label className="block text-sm font-medium mb-2">Caption</label>
                <textarea
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-3 h-28 resize-none"
                  value={formData.caption}
                  onChange={(e) => setFormData((s) => ({ ...s, caption: e.target.value }))}
                />
              </div>

              {/* SCHEDULE */}
              <div>
                <label className="block text-sm font-medium mb-1">Schedule (optional)</label>
                <input
                  type="datetime-local"
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-3"
                  value={formData.scheduled_time}
                  onChange={(e) => setFormData((s) => ({ ...s, scheduled_time: e.target.value }))}
                />
              </div>

              {/* BUTTONS */}
              <div className="flex gap-3 pt-3">
                <button className="flex-1 py-2 border border-white/10 rounded-lg bg-white/5" onClick={resetForm}>
                  Cancel
                </button>

                <button
                  className="flex-1 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 disabled:opacity-50"
                  disabled={!formData.caption || !formData.image}
                  onClick={editingPost ? handleUpdatePost : handleCreatePost}
                >
                  {editingPost ? "Update" : "Create"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
