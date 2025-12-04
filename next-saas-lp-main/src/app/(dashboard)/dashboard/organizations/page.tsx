"use client";

import { Plus, Users, Settings, Crown, Mail, MoreHorizontal, Edit2, Trash2, UserPlus } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { organizationsAPI, Organization, CreateOrganizationData } from "@/lib/api/organizations";
import { brandsAPI } from "@/lib/api/brands";

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [deletingOrg, setDeletingOrg] = useState<Organization | null>(null);
  const [invitingToOrg, setInvitingToOrg] = useState<Organization | null>(null);
  const [formData, setFormData] = useState<CreateOrganizationData>({
    name: "",
  });
  const [inviteData, setInviteData] = useState({
    email: "",
    role: "member" as "admin" | "member",
    message: "",
  });

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      const data = await organizationsAPI.getOrganizations();
      setOrganizations(data);
    } catch (error) {
      console.error("Failed to load organizations:", error);
      toast.error("Failed to load organizations");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("Organization name is required");
      return;
    }

    setCreateLoading(true);
    try {
      await organizationsAPI.createOrganization(formData);
      toast.success("Organization created successfully");
      setShowCreateModal(false);
      setFormData({ name: "" });
      loadOrganizations();
    } catch (error: any) {
      console.error("Failed to create organization:", error);
      toast.error(error.message || "Failed to create organization");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteOrganization = (org: Organization) => {
    setDeletingOrg(org);
    setShowDeleteModal(true);
  };

  const confirmDeleteOrganization = async () => {
    if (!deletingOrg) return;

    setDeleteLoading(true);
    try {
      await organizationsAPI.deleteOrganization(deletingOrg.id);
      toast.success("Organization deleted successfully");
      loadOrganizations();
      setShowDeleteModal(false);
      setDeletingOrg(null);
    } catch (error: any) {
      console.error("Failed to delete organization:", error);
      toast.error(error.message || "Failed to delete organization");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleInviteUser = (org: Organization) => {
    setInvitingToOrg(org);
    setInviteData({ email: "", role: "member", message: "" });
    setShowInviteModal(true);
  };

  const sendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invitingToOrg) return;

    if (!inviteData.email.trim()) {
      toast.error("Email is required");
      return;
    }

    setInviteLoading(true);
    try {
      await organizationsAPI.inviteUser(invitingToOrg.id, {
        email: inviteData.email,
        role: inviteData.role,
        message: inviteData.message,
      });
      toast.success(`Invitation sent to ${inviteData.email}`);
      setShowInviteModal(false);
      setInvitingToOrg(null);
      setInviteData({ email: "", role: "member", message: "" });
    } catch (error: any) {
      console.error("Failed to send invitation:", error);
      toast.error(error.message || "Failed to send invitation");
    } finally {
      setInviteLoading(false);
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Organizations</h1>
          <p className="text-gray-400 mt-1">
            Manage your teams and collaborate with your organization members
          </p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Organization
        </button>
      </div>

      {/* Organizations Grid */}
      {organizations.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {organizations.map((org) => (
            <div
              key={org.id}
              className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors"
            >
              {/* Organization Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                    {org.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-lg">{org.name}</h3>
                      {org.is_admin && (
                        <Crown className="w-4 h-4 text-yellow-400" title="Admin" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400">
                      {org.is_admin ? "Administrator" : "Member"}
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-1">
                  {org.is_admin && (
                    <>
                      <button
                        onClick={() => handleInviteUser(org)}
                        className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                        title="Invite user"
                      >
                        <UserPlus className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteOrganization(org)}
                        className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-red-400"
                        title="Delete organization"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Organization Stats */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-gray-400">
                    <Users className="w-4 h-4" />
                    Members
                  </span>
                  <span className="font-medium">{org.member_count || 1}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2 text-gray-400">
                    <Settings className="w-4 h-4" />
                    Created
                  </span>
                  <span className="font-medium">
                    {new Date(org.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-2">
                <Link
                  href={`/dashboard/organizations/${org.id}`}
                  className="flex-1 bg-white/5 border border-white/10 hover:bg-white/10 text-center py-2 px-3 rounded text-sm transition-colors"
                >
                  View Details
                </Link>
                <Link
                  href={`/dashboard/brands?org=${org.id}`}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-center py-2 px-3 rounded text-sm transition-colors text-white"
                >
                  View Brands
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
            <Users className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-bold mb-2">No Organizations Yet</h3>
          <p className="text-gray-400 mb-6">
            Create your first organization to start collaborating with your team
          </p>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity"
          >
            Create Organization
          </button>
        </div>
      )}

      {/* Create Organization Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Create New Organization</h2>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateOrganization} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Organization Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter organization name"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">
                  You will be the administrator of this organization
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 py-2 px-4 rounded-lg transition-opacity font-medium"
                >
                  {createLoading ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingOrg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-red-400">Delete Organization</h2>
              <button 
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingOrg(null);
                }}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="mb-6">
              <p className="text-gray-300 mb-2">
                Are you sure you want to delete "{deletingOrg.name}"?
              </p>
              <p className="text-sm text-red-400">
                This will also delete all associated brands and data. This action cannot be undone.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingOrg(null);
                }}
                className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteOrganization}
                disabled={deleteLoading}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 py-2 px-4 rounded-lg transition-colors font-medium"
              >
                {deleteLoading ? "Deleting..." : "Delete Organization"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Invite User Modal */}
      {showInviteModal && invitingToOrg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Invite User to {invitingToOrg.name}</h2>
              <button 
                onClick={() => {
                  setShowInviteModal(false);
                  setInvitingToOrg(null);
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
                    setInvitingToOrg(null);
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
    </div>
  );
}