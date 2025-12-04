"use client";

import { ArrowLeft, Users, Crown, Settings, Edit2, UserPlus, UserMinus, Trash2, Twitter, Instagram, Globe, Plus } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { organizationsAPI, Organization, OrganizationMember } from "@/lib/api/organizations";
import { brandsAPI, Brand } from "@/lib/api/brands";

interface Props {
  params: Promise<{ id: string }>;
}

export default function OrganizationDetailPage({ params }: Props) {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showRemoveModal, setShowRemoveModal] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [removeLoading, setRemoveLoading] = useState(false);
  const [removingMember, setRemovingMember] = useState<OrganizationMember | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [inviteData, setInviteData] = useState({
    email: "",
    role: "member" as "admin" | "member",
    message: "",
  });

  useEffect(() => {
    params.then(p => {
      setOrgId(p.id);
    });
  }, [params]);

  useEffect(() => {
    if (orgId) {
      loadOrganizationData();
    }
  }, [orgId]);

  const loadOrganizationData = async () => {
    if (!orgId) return;
    
    try {
      const [orgData, membersData, brandsData] = await Promise.all([
        organizationsAPI.getOrganization(parseInt(orgId)),
        organizationsAPI.getOrganizationMembers(parseInt(orgId)),
        organizationsAPI.getOrganizationBrands(parseInt(orgId)),
      ]);
      
      setOrganization(orgData);
      setMembers(membersData);
      setBrands(brandsData);
    } catch (error) {
      console.error("Failed to load organization data:", error);
      toast.error("Failed to load organization data");
    } finally {
      setLoading(false);
    }
  };

  const sendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!organization) return;

    if (!inviteData.email.trim()) {
      toast.error("Email is required");
      return;
    }

    setInviteLoading(true);
    try {
      await organizationsAPI.inviteUser(organization.id, {
        email: inviteData.email,
        role: inviteData.role,
        message: inviteData.message,
      });
      toast.success(`Invitation sent to ${inviteData.email}`);
      setShowInviteModal(false);
      setInviteData({ email: "", role: "member", message: "" });
    } catch (error: any) {
      console.error("Failed to send invitation:", error);
      toast.error(error.message || "Failed to send invitation");
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRemoveMember = (member: OrganizationMember) => {
    setRemovingMember(member);
    setShowRemoveModal(true);
  };

  const confirmRemoveMember = async () => {
    if (!removingMember || !organization) return;

    setRemoveLoading(true);
    try {
      await organizationsAPI.removeMember(organization.id, removingMember.id);
      toast.success(`${removingMember.user.email} removed from organization`);
      setShowRemoveModal(false);
      setRemovingMember(null);
      loadOrganizationData(); // Reload data
    } catch (error: any) {
      console.error("Failed to remove member:", error);
      toast.error(error.message || "Failed to remove member");
    } finally {
      setRemoveLoading(false);
    }
  };

  const updateMemberRole = async (memberId: number, newRole: "admin" | "member") => {
    if (!organization) return;

    try {
      await organizationsAPI.updateMemberRole(organization.id, memberId, newRole);
      toast.success("Member role updated successfully");
      loadOrganizationData(); // Reload data
    } catch (error: any) {
      console.error("Failed to update member role:", error);
      toast.error(error.message || "Failed to update member role");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold mb-2">Organization not found</h2>
        <Link href="/dashboard/organizations" className="text-blue-400 hover:underline">
          ← Back to Organizations
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/dashboard/organizations"
          className="p-2 hover:bg-white/5 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex items-center gap-4 flex-1">
          <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl">
            {organization.name.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold">{organization.name}</h1>
              {organization.is_admin && (
                <Crown className="w-6 h-6 text-yellow-400" title="Admin" />
              )}
            </div>
            <p className="text-gray-400">
              {organization.is_admin ? "Administrator" : "Member"} • {members.length} member{members.length !== 1 ? 's' : ''} • {brands.length} brand{brands.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        {organization.is_admin && (
          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center gap-2"
          >
            <UserPlus className="w-5 h-5" />
            Invite Member
          </button>
        )}
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold">Team Members</h3>
          </div>
          <p className="text-2xl font-bold">{members.length}</p>
          <p className="text-sm text-gray-400">
            {members.filter(m => m.role === 'admin').length} admin{members.filter(m => m.role === 'admin').length !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Globe className="w-5 h-5 text-green-400" />
            <h3 className="font-semibold">Active Brands</h3>
          </div>
          <p className="text-2xl font-bold">{brands.length}</p>
          <p className="text-sm text-gray-400">
            {brands.filter(b => b.has_twitter_config || b.has_instagram_config).length} connected
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <Settings className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold">Created</h3>
          </div>
          <p className="text-2xl font-bold">{new Date(organization.created_at).toLocaleDateString()}</p>
          <p className="text-sm text-gray-400">Organization established</p>
        </div>
      </div>

      {/* Team Members Section */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Team Members</h2>
          {organization.is_admin && (
            <button
              onClick={() => setShowInviteModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <UserPlus className="w-4 h-4" />
              Invite Member
            </button>
          )}
        </div>

        <div className="space-y-3">
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                  {member.user.email.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{member.user.email}</p>
                    {member.role === 'admin' && (
                      <Crown className="w-4 h-4 text-yellow-400" title="Admin" />
                    )}
                  </div>
                  <p className="text-sm text-gray-400">
                    {member.role === 'admin' ? 'Administrator' : 'Member'} • 
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {organization.is_admin && member.user.id !== organization.owner?.id && (
                <div className="flex items-center gap-2">
                  <select
                    value={member.role}
                    onChange={(e) => updateMemberRole(member.id, e.target.value as "admin" | "member")}
                    className="bg-white/5 border border-white/10 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                  <button
                    onClick={() => handleRemoveMember(member)}
                    className="p-2 hover:bg-red-500/20 rounded-lg transition-colors text-gray-400 hover:text-red-400"
                    title="Remove member"
                  >
                    <UserMinus className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Brands Section */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Organization Brands</h2>
          <Link
            href={`/dashboard/brands?create=true&org=${organization.id}`}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-opacity flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Brand
          </Link>
        </div>

        {brands.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {brands.map((brand) => (
              <div
                key={brand.id}
                className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                      {brand.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold">{brand.name}</h3>
                        {brand.is_default && (
                          <span className="bg-yellow-500/20 text-yellow-400 text-xs px-2 py-1 rounded-full">
                            Default
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400">{brand.description || "No description"}</p>
                    </div>
                  </div>
                  <Link
                    href={`/dashboard/brands/${brand.slug}`}
                    className="text-blue-400 hover:text-blue-300 text-sm"
                  >
                    View →
                  </Link>
                </div>

                {/* Brand connections */}
                <div className="space-y-1 mb-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1">
                      <Instagram className="w-3 h-3" />
                      Instagram
                    </span>
                    <span className={`px-2 py-1 rounded-full ${brand.has_instagram_config ? "bg-green-500/20 text-green-400" : "bg-gray-500/20 text-gray-400"}`}>
                      {brand.has_instagram_config ? "Connected" : "Not Connected"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1">
                      <Twitter className="w-3 h-3" />
                      Twitter
                    </span>
                    <span className={`px-2 py-1 rounded-full ${brand.has_twitter_config ? "bg-green-500/20 text-green-400" : "bg-gray-500/20 text-gray-400"}`}>
                      {brand.has_twitter_config ? "Connected" : "Not Connected"}
                    </span>
                  </div>
                </div>

                {/* Brand actions */}
                <div className="flex gap-2">
                  <Link
                    href={`/dashboard/brands/${brand.slug}/instagram`}
                    className="flex-1 bg-white/5 border border-white/10 hover:bg-white/10 text-center py-2 px-3 rounded text-xs transition-colors"
                  >
                    Instagram
                  </Link>
                  <Link
                    href={`/dashboard/brands/${brand.slug}/twitter`}
                    className="flex-1 bg-white/5 border border-white/10 hover:bg-white/10 text-center py-2 px-3 rounded text-xs transition-colors"
                  >
                    Twitter
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 border border-dashed border-white/20 rounded-lg">
            <Globe className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Brands Yet</h3>
            <p className="text-gray-400 mb-4">Create your first brand to start managing social media for this organization</p>
            <Link
              href={`/dashboard/brands?create=true&org=${organization.id}`}
              className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-opacity"
            >
              Create First Brand
            </Link>
          </div>
        )}
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Invite Member to {organization.name}</h2>
              <button 
                onClick={() => {
                  setShowInviteModal(false);
                  setInviteData({ email: "", role: "member", message: "" });
                }}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={sendInvitation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Email Address *</label>
                <input
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="colleague@company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Role</label>
                <select
                  value={inviteData.role}
                  onChange={(e) => setInviteData({ ...inviteData, role: e.target.value as "admin" | "member" })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="member">Member</option>
                  <option value="admin">Administrator</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Administrators can manage the organization and invite others
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Personal Message (Optional)</label>
                <textarea
                  value={inviteData.message}
                  onChange={(e) => setInviteData({ ...inviteData, message: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-20 resize-none"
                  placeholder="Add a personal message to the invitation..."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteData({ email: "", role: "member", message: "" });
                  }}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500 hover:opacity-90 disabled:opacity-50 py-2 px-4 rounded-lg transition-opacity font-medium"
                >
                  {inviteLoading ? "Sending..." : "Send Invitation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Remove Member Modal */}
      {showRemoveModal && removingMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-red-400">Remove Member</h2>
              <button 
                onClick={() => {
                  setShowRemoveModal(false);
                  setRemovingMember(null);
                }}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="mb-6">
              <p className="text-gray-300 mb-2">
                Are you sure you want to remove {removingMember.user.email} from {organization.name}?
              </p>
              <p className="text-sm text-red-400">
                They will lose access to all organization brands and data.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowRemoveModal(false);
                  setRemovingMember(null);
                }}
                className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmRemoveMember}
                disabled={removeLoading}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 py-2 px-4 rounded-lg transition-colors font-medium"
              >
                {removeLoading ? "Removing..." : "Remove Member"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}