"use client";

import { User, Mail, Lock, Bell, Globe, Shield, CreditCard, Camera, DollarSign, TrendingUp, Package, Receipt, Plus, CheckCircle, Clock, XCircle, Download, Calendar } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { getCurrentUser } from "@/lib/auth";
import type { User as UserType } from "@/lib/auth";
import { userApi, type UserProfile } from "@/lib/user-api";
import { toast } from "sonner";

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<
    "profile" | "account" | "notifications" | "security" | "billing"
  >("profile");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form states
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [bio, setBio] = useState("");
  const [instagramHandle, setInstagramHandle] = useState("");
  const [age, setAge] = useState("");

  // Password change states
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const data = await userApi.getCurrentProfile();
      setUser(data);
      setFirstName(data.first_name || "");
      setLastName(data.last_name || "");
      setBio(data.bio || "");
      setInstagramHandle(data.instagram_handle || "");
      setAge(data.age?.toString() || "");
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleProfilePictureUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Image must be less than 2MB');
      return;
    }

    try {
      setUploading(true);
      
      // Upload image
      const { url } = await userApi.uploadProfilePicture(file);
      
      // Update profile with new image URL
      const updatedUser = await userApi.updateProfile({
        profile_picture_url: url,
      });
      
      setUser(updatedUser);
      toast.success('Profile picture updated successfully!');
    } catch (err) {
      console.error('Error uploading profile picture:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to upload profile picture');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const updatedUser = await userApi.updateProfile({
        first_name: firstName,
        last_name: lastName,
        bio: bio,
        instagram_handle: instagramHandle,
        age: age ? parseInt(age) : null,
      });

      setUser(updatedUser);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while updating your profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    try {
      setChangingPassword(true);
      setPasswordError(null);
      setPasswordSuccess(null);

      // Validation
      if (!currentPassword || !newPassword || !confirmPassword) {
        setPasswordError('All fields are required');
        return;
      }

      if (newPassword !== confirmPassword) {
        setPasswordError('New passwords do not match');
        return;
      }

      if (newPassword.length < 8) {
        setPasswordError('Password must be at least 8 characters');
        return;
      }

      const authToken = localStorage.getItem('auth_token');

      const response = await fetch(`${DJANGO_BACKEND}/api/auth/password/change/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { 'Authorization': `Token ${authToken}` }),
        },
        body: JSON.stringify({
          old_password: currentPassword,
          new_password1: newPassword,
          new_password2: confirmPassword,
        }),
      });

      if (response.ok) {
        setPasswordSuccess('Password updated successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => setPasswordSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setPasswordError(errorData.old_password?.[0] || errorData.new_password2?.[0] || 'Failed to update password');
      }
    } catch (err) {
      console.error('Error changing password:', err);
      setPasswordError('An error occurred while changing your password');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-gray-400 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white/5 border border-white/10 rounded-lg p-2 space-y-1">
            <button
              onClick={() => setActiveTab("profile")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                activeTab === "profile"
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-gray-400 hover:bg-white/5"
              }`}
            >
              <User className="w-4 h-4" />
              Profile
            </button>
            <button
              onClick={() => setActiveTab("account")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                activeTab === "account"
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-gray-400 hover:bg-white/5"
              }`}
            >
              <Mail className="w-4 h-4" />
              Account
            </button>
            <button
              onClick={() => setActiveTab("notifications")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                activeTab === "notifications"
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-gray-400 hover:bg-white/5"
              }`}
            >
              <Bell className="w-4 h-4" />
              Notifications
            </button>
            <button
              onClick={() => setActiveTab("security")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                activeTab === "security"
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-gray-400 hover:bg-white/5"
              }`}
            >
              <Shield className="w-4 h-4" />
              Security
            </button>
            <button
              onClick={() => setActiveTab("billing")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                activeTab === "billing"
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-gray-400 hover:bg-white/5"
              }`}
            >
              <CreditCard className="w-4 h-4" />
              Billing
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {activeTab === "profile" && (
            <div className="bg-white/5 border border-white/10 rounded-lg p-6 space-y-6">
              <div>
                <h2 className="text-xl font-bold mb-4">Profile Information</h2>
                <p className="text-sm text-gray-400 mb-6">
                  Update your profile information and photo
                </p>

                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    {error}
                  </div>
                )}

                {success && (
                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
                    {success}
                  </div>
                )}

                {/* Avatar */}
                <div className="flex items-center gap-6 mb-6">
                  <div className="relative">
                    {user?.profile_picture ? (
                      <img
                        src={user.profile_picture}
                        alt="Profile"
                        className="w-20 h-20 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-2xl font-bold">
                        {firstName?.[0] || user?.username?.[0] || 'U'}
                      </div>
                    )}
                    {uploading && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                      </div>
                    )}
                  </div>
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleProfilePictureUpload}
                      className="hidden"
                    />
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="bg-white/5 border border-white/10 hover:bg-white/10 px-4 py-2 rounded-lg text-sm transition-colors mb-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Camera className="w-4 h-4" />
                      {uploading ? 'Uploading...' : 'Change Photo'}
                    </button>
                    <p className="text-xs text-gray-400">
                      JPG, PNG or GIF. Max 2MB.
                    </p>
                  </div>
                </div>

                {/* Form */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Bio
                    </label>
                    <textarea
                      rows={4}
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell us about yourself..."
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Instagram Handle
                    </label>
                    <input
                      type="text"
                      value={instagramHandle}
                      onChange={(e) => setInstagramHandle(e.target.value)}
                      placeholder="@yourusername"
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Age
                    </label>
                    <input
                      type="number"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="25"
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <button 
                    onClick={() => fetchUserProfile()}
                    className="bg-white/5 border border-white/10 hover:bg-white/10 px-6 py-2 rounded-lg text-sm transition-colors"
                    disabled={saving}
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleSaveProfile}
                    disabled={saving}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-2 rounded-lg text-sm transition-opacity disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === "account" && (
            <div className="space-y-6">
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <h2 className="text-xl font-bold mb-4">Account Settings</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 opacity-60 cursor-not-allowed"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Email cannot be changed
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      value={user?.username || ''}
                      disabled
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 opacity-60 cursor-not-allowed"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Username cannot be changed
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Member Since
                    </label>
                    <input
                      type="text"
                      value={user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      }) : 'N/A'}
                      disabled
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 opacity-60 cursor-not-allowed"
                    />
                  </div>

                  {user?.impressions_count !== undefined && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Profile Views
                      </label>
                      <input
                        type="text"
                        value={user.impressions_count.toLocaleString()}
                        disabled
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 opacity-60 cursor-not-allowed"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
                <h3 className="text-lg font-bold text-red-400 mb-2">
                  Danger Zone
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  Once you delete your account, there is no going back. Please
                  be certain.
                </p>
                <button className="bg-red-500/20 text-red-400 hover:bg-red-500/30 px-4 py-2 rounded-lg text-sm transition-colors">
                  Delete Account
                </button>
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Notification Preferences</h2>
              <p className="text-sm text-gray-400 mb-6">
                Choose what notifications you want to receive
              </p>

              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-3">Email Notifications</h3>
                  <div className="space-y-3">
                    {[
                      { label: "Post Performance Updates", checked: true },
                      { label: "Weekly Analytics Report", checked: true },
                      { label: "New Followers", checked: false },
                      { label: "Comments & Mentions", checked: true },
                    ].map((item, idx) => (
                      <label
                        key={idx}
                        className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                      >
                        <span className="text-sm">{item.label}</span>
                        <input
                          type="checkbox"
                          defaultChecked={item.checked}
                          className="w-4 h-4"
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-3">Push Notifications</h3>
                  <div className="space-y-3">
                    {[
                      { label: "Post Published", checked: true },
                      { label: "Scheduled Post Reminder", checked: true },
                      { label: "Team Activity", checked: false },
                    ].map((item, idx) => (
                      <label
                        key={idx}
                        className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                      >
                        <span className="text-sm">{item.label}</span>
                        <input
                          type="checkbox"
                          defaultChecked={item.checked}
                          className="w-4 h-4"
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-2 rounded-lg text-sm transition-opacity">
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <h2 className="text-xl font-bold mb-4">Change Password</h2>

                {passwordError && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    {passwordError}
                  </div>
                )}

                {passwordSuccess && (
                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
                    {passwordSuccess}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Current Password
                    </label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button 
                    onClick={handlePasswordChange}
                    disabled={changingPassword}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-2 rounded-lg text-sm transition-opacity disabled:opacity-50"
                  >
                    {changingPassword ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <h3 className="font-bold mb-2">Two-Factor Authentication</h3>
                <p className="text-sm text-gray-400 mb-4">
                  Add an extra layer of security to your account
                </p>
                <button className="bg-white/5 border border-white/10 hover:bg-white/10 px-4 py-2 rounded-lg text-sm transition-colors">
                  Enable 2FA
                </button>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <h3 className="font-bold mb-2">Active Sessions</h3>
                <p className="text-sm text-gray-400 mb-4">
                  Manage your active sessions across devices
                </p>
                <div className="space-y-3">
                  {[
                    {
                      device: "Windows PC",
                      location: "New York, US",
                      current: true,
                    },
                    {
                      device: "iPhone 14",
                      location: "New York, US",
                      current: false,
                    },
                  ].map((session, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-sm flex items-center gap-2">
                          {session.device}
                          {session.current && (
                            <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full text-xs">
                              Current
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400">
                          {session.location}
                        </div>
                      </div>
                      {!session.current && (
                        <button className="text-sm text-red-400 hover:text-red-300">
                          Revoke
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "billing" && (
            <BillingContent />
          )}
        </div>
      </div>
    </div>
  );
}

// Billing Content Component
function BillingContent() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  interface PlanFeature {
    text: string;
    included: boolean;
  }

  interface Plan {
    id: string;
    name: string;
    price: number;
    credits: number;
    features: PlanFeature[];
    popular?: boolean;
  }

  interface Transaction {
    id: string;
    date: string;
    description: string;
    amount: number;
    credits: number;
    status: 'completed' | 'pending' | 'failed';
    invoice_url?: string;
  }

  const PLANS: Plan[] = [
    {
      id: 'starter',
      name: 'Starter Pack',
      price: 9.99,
      credits: 100,
      features: [
        { text: '100 AI Credits', included: true },
        { text: 'Basic Instagram Management', included: true },
        { text: 'Content Generation', included: true },
        { text: 'Email Support', included: true },
        { text: 'Advanced Analytics', included: false },
        { text: 'Priority Support', included: false },
      ]
    },
    {
      id: 'growth',
      name: 'Growth Pack',
      price: 29.99,
      credits: 350,
      features: [
        { text: '350 AI Credits', included: true },
        { text: 'Advanced Instagram Management', included: true },
        { text: 'Content Generation + Optimization', included: true },
        { text: 'Advanced Analytics', included: true },
        { text: 'Priority Email Support', included: true },
        { text: 'Custom Branding', included: false },
      ],
      popular: true
    },
    {
      id: 'pro',
      name: 'Pro Pack',
      price: 59.99,
      credits: 750,
      features: [
        { text: '750 AI Credits', included: true },
        { text: 'Full Instagram Suite', included: true },
        { text: 'AI Content Creation & Optimization', included: true },
        { text: 'Advanced Analytics & Reporting', included: true },
        { text: '24/7 Priority Support', included: true },
        { text: 'Custom Branding & White-label', included: true },
      ]
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 149.99,
      credits: 2000,
      features: [
        { text: '2000+ AI Credits', included: true },
        { text: 'Enterprise Instagram Management', included: true },
        { text: 'Custom AI Models & Training', included: true },
        { text: 'Advanced Analytics & API Access', included: true },
        { text: 'Dedicated Account Manager', included: true },
        { text: 'Full White-label & Custom Integration', included: true },
      ]
    }
  ];

  const MOCK_TRANSACTIONS: Transaction[] = [
    {
      id: 'tx_001',
      date: '2024-11-29',
      description: 'Growth Pack - 350 AI Credits',
      amount: 29.99,
      credits: 350,
      status: 'completed',
      invoice_url: '/invoices/tx_001.pdf'
    },
    {
      id: 'tx_002', 
      date: '2024-11-15',
      description: 'Starter Pack - 100 AI Credits',
      amount: 9.99,
      credits: 100,
      status: 'completed',
      invoice_url: '/invoices/tx_002.pdf'
    },
    {
      id: 'tx_003',
      date: '2024-11-01',
      description: 'Pro Pack - 750 AI Credits',
      amount: 59.99,
      credits: 750,
      status: 'completed',
      invoice_url: '/invoices/tx_003.pdf'
    },
    {
      id: 'tx_004',
      date: '2024-10-28',
      description: 'Growth Pack - 350 AI Credits',
      amount: 29.99,
      credits: 350,
      status: 'pending'
    },
    {
      id: 'tx_005',
      date: '2024-10-15',
      description: 'Starter Pack - 100 AI Credits',
      amount: 9.99,
      credits: 100,
      status: 'failed'
    }
  ];

  // Mock user data - in real app this would come from API
  const userCredits = {
    current: 245,
    total_purchased: 1450,
    total_used: 1205,
    last_updated: '2024-11-29'
  };

  const handlePurchase = async (planId: string) => {
    setIsLoading(true);
    setSelectedPlan(planId);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const plan = PLANS.find(p => p.id === planId);
      toast.success(`Successfully purchased ${plan?.name}! ${plan?.credits} credits added to your account.`);
      
      // In real app, redirect to payment processor or show success
    } catch (error) {
      toast.error('Payment failed. Please try again.');
    } finally {
      setIsLoading(false);
      setSelectedPlan(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusIcon = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusColor = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-500/10';
      case 'pending':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'failed':
        return 'text-red-400 bg-red-500/10';
    }
  };

  return (
    <div className="space-y-8">
      {/* Credits Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Current Credits</h3>
              <p className="text-2xl font-bold text-purple-400">{userCredits.current}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Last updated: {formatDate(userCredits.last_updated)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Total Purchased</h3>
              <p className="text-2xl font-bold text-blue-400">{userCredits.total_purchased.toLocaleString()}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Lifetime credits purchased
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Package className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Credits Used</h3>
              <p className="text-2xl font-bold text-green-400">{userCredits.total_used.toLocaleString()}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Total credits consumed
          </div>
        </div>
      </div>

      {/* Usage Progress */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">Credit Usage</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Available Credits</span>
            <span className="font-medium">{userCredits.current} remaining</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500"
              style={{ 
                width: `${Math.max(10, (userCredits.current / (userCredits.current + 100)) * 100)}%` 
              }}
            />
          </div>
          <div className="text-xs text-gray-400">
            Consider purchasing more credits when you reach 50 credits or below
          </div>
        </div>
      </div>

      {/* Purchase Plans */}
      <div>
        <h2 className="text-xl font-bold mb-6">Purchase More Credits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white/5 border rounded-lg p-6 transition-all duration-300 hover:bg-white/10 ${
                plan.popular 
                  ? 'border-purple-500/50 ring-2 ring-purple-500/20' 
                  : 'border-white/10 hover:border-purple-500/30'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-lg font-bold mb-2">{plan.name}</h3>
                <div className="text-3xl font-bold mb-1">
                  <span className="text-sm font-normal">$</span>
                  {plan.price}
                </div>
                <div className="text-sm text-gray-400 mb-4">
                  {plan.credits} AI Credits
                </div>
                <div className="text-xs text-purple-400 bg-purple-500/10 rounded-full px-3 py-1 inline-block">
                  ${(plan.price / plan.credits).toFixed(3)}/credit
                </div>
              </div>

              <div className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    {feature.included ? (
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    )}
                    <span className={feature.included ? 'text-gray-300' : 'text-gray-500'}>
                      {feature.text}
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handlePurchase(plan.id)}
                disabled={isLoading}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
                  plan.popular
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:opacity-90'
                    : 'bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:border-purple-500/30'
                }`}
              >
                {isLoading && selectedPlan === plan.id ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Processing...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <Plus className="w-4 h-4" />
                    Purchase Now
                  </div>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Transaction History */}
      <div className="bg-white/5 border border-white/10 rounded-lg overflow-hidden">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold">Transaction History</h3>
            <button className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1">
              <Download className="w-4 h-4" />
              Export All
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white/5">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Date</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Description</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Credits</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Amount</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {MOCK_TRANSACTIONS.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-white/5">
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-sm">{formatDate(transaction.date)}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm font-medium">{transaction.description}</div>
                    <div className="text-xs text-gray-400">Transaction ID: {transaction.id}</div>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-purple-400">
                      +{transaction.credits}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium">${transaction.amount}</span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(transaction.status)}
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(transaction.status)}`}>
                        {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {transaction.invoice_url && transaction.status === 'completed' && (
                        <button 
                          onClick={() => window.open(transaction.invoice_url, '_blank')}
                          className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                        >
                          <Receipt className="w-3 h-3" />
                          Invoice
                        </button>
                      )}
                      {transaction.status === 'failed' && (
                        <button 
                          onClick={() => handlePurchase('retry')}
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          Retry
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Billing Information */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">Billing Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-400">
              Payment Method
            </label>
            <div className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg">
              <CreditCard className="w-5 h-5 text-gray-400" />
              <div>
                <div className="text-sm font-medium">**** **** **** 4242</div>
                <div className="text-xs text-gray-400">Expires 12/2025</div>
              </div>
              <button className="ml-auto text-xs text-purple-400 hover:text-purple-300">
                Update
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-400">
              Billing Address
            </label>
            <div className="space-y-2 text-sm text-gray-300">
              <div>John Doe</div>
              <div>123 Main Street, Apt 4B</div>
              <div>New York, NY 10001</div>
              <div>United States</div>
            </div>
            <button className="mt-2 text-xs text-purple-400 hover:text-purple-300">
              Update Address
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
