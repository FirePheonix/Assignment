"use client";

import { Plus, Twitter, Instagram, Globe, Settings, X, Edit2, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { brandsAPI, Brand, CreateBrandData } from "@/lib/api/brands";
import { organizationsAPI, Organization, CreateOrganizationData } from "@/lib/api/organizations";

export default function BrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showEditOrgModal, setShowEditOrgModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createOrgLoading, setCreateOrgLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [deletingBrand, setDeletingBrand] = useState<Brand | null>(null);
  const [formData, setFormData] = useState<CreateBrandData>({
    name: "",
    description: "",
    url: "",
    organization_id: null,
  });
  const [orgFormData, setOrgFormData] = useState<CreateOrganizationData>({
    name: "",
  });

  useEffect(() => {
    loadBrands();
    loadOrganizations();
  }, []);

  const loadBrands = async () => {
    try {
      const data = await brandsAPI.getBrands();
      setBrands(data);
    } catch (error) {
      console.error("Failed to load brands:", error);
      toast.error("Failed to load brands");
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizations = async () => {
    try {
      const data = await organizationsAPI.getOrganizations();
      setOrganizations(data);
    } catch (error) {
      console.error("Failed to load organizations:", error);
      // Don't show error toast for organizations as it's optional
    }
  };

  const handleCreateBrand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("Brand name is required");
      return;
    }
    if (!formData.url?.trim()) {
      toast.error("Website URL is required");
      return;
    }

    setCreateLoading(true);
    try {
      await brandsAPI.createBrand(formData);
      toast.success("Brand created successfully");
      setShowCreateModal(false);
      setFormData({ name: "", description: "", url: "", organization_id: null });
      loadBrands(); // Reload brands
    } catch (error: any) {
      console.error("Failed to create brand:", error);
      toast.error(error.message || "Failed to create brand");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleSetDefault = async (brandId: number) => {
    try {
      await brandsAPI.setDefaultBrand(brandId);
      toast.success("Default brand updated");
      loadBrands(); // Reload to see updated default status
    } catch (error: any) {
      console.error("Failed to set default brand:", error);
      toast.error(error.message || "Failed to set default brand");
    }
  };

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgFormData.name.trim()) {
      toast.error("Organization name is required");
      return;
    }

    setCreateOrgLoading(true);
    try {
      await organizationsAPI.createOrganization(orgFormData);
      toast.success("Organization created successfully");
      setShowCreateOrgModal(false);
      setOrgFormData({ name: "" });
      loadOrganizations(); // Reload organizations
    } catch (error: any) {
      console.error("Failed to create organization:", error);
      toast.error(error.message || "Failed to create organization");
    } finally {
      setCreateOrgLoading(false);
    }
  };

  const handleEditBrand = (brand: Brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || "",
      url: brand.url || "",
      organization_id: brand.organization_id,
    });
    setShowEditModal(true);
  };

  const handleUpdateBrand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingBrand) return;

    if (!formData.name.trim()) {
      toast.error("Brand name is required");
      return;
    }
    if (!formData.url?.trim()) {
      toast.error("Website URL is required");
      return;
    }

    setCreateLoading(true);
    try {
      await brandsAPI.updateBrand(editingBrand.id, formData);
      toast.success("Brand updated successfully");
      setShowEditModal(false);
      setEditingBrand(null);
      loadBrands();
    } catch (error: any) {
      console.error("Failed to update brand:", error);
      toast.error(error.message || "Failed to update brand");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteBrand = (brand: Brand) => {
    setDeletingBrand(brand);
    setShowDeleteModal(true);
  };

  const confirmDeleteBrand = async () => {
    if (!deletingBrand) return;

    setDeleteLoading(true);
    try {
      await brandsAPI.deleteBrand(deletingBrand.id);
      toast.success("Brand deleted successfully");
      loadBrands();
      setShowDeleteModal(false);
      setDeletingBrand(null);
    } catch (error: any) {
      console.error("Failed to delete brand:", error);
      toast.error(error.message || "Failed to delete brand");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleEditOrganization = (org: Organization) => {
    setEditingOrg(org);
    setOrgFormData({ name: org.name });
    setShowEditOrgModal(true);
  };

  const handleUpdateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingOrg) return;

    if (!orgFormData.name.trim()) {
      toast.error("Organization name is required");
      return;
    }

    setCreateOrgLoading(true);
    try {
      await organizationsAPI.updateOrganization(editingOrg.id, orgFormData);
      toast.success("Organization updated successfully");
      setShowEditOrgModal(false);
      setEditingOrg(null);
      loadOrganizations();
    } catch (error: any) {
      console.error("Failed to update organization:", error);
      toast.error(error.message || "Failed to update organization");
    } finally {
      setCreateOrgLoading(false);
    }
  };

  const handleDeleteOrganization = async (org: Organization) => {
    if (!confirm(`Are you sure you want to delete "${org.name}"? This will also delete all associated brands. This action cannot be undone.`)) {
      return;
    }

    try {
      await organizationsAPI.deleteOrganization(org.id);
      toast.success("Organization deleted successfully");
      loadOrganizations();
      loadBrands(); // Refresh brands as well
    } catch (error: any) {
      console.error("Failed to delete organization:", error);
      toast.error(error.message || "Failed to delete organization");
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
          <h1 className="text-3xl font-bold">Brand Management</h1>
          <p className="text-gray-400 mt-1">
            Manage your brands and social media accounts
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setShowCreateOrgModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Organization
          </button>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Brand
          </button>
        </div>
      </div>

      {/* Organizations and their Brands */}
      {organizations.length > 0 && (
        <div className="space-y-8">
          {organizations.map((org) => {
            const orgBrands = brands.filter(brand => brand.organization_id === org.id);
            return (
              <div key={org.id} className="bg-white/5 border border-white/10 rounded-lg p-6">
                {/* Organization Header */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-sm font-bold">
                        {org.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h2 className="text-xl font-bold">{org.name}</h2>
                        <p className="text-sm text-gray-400">
                          {org.is_admin ? "Administrator" : "Member"} • {orgBrands.length} brand{orgBrands.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setFormData({ name: '', description: '', url: '', organization_id: org.id });
                        setShowCreateModal(true);
                      }}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-opacity text-sm"
                    >
                      Add Brand
                    </button>
                    {org.is_admin && (
                      <button
                        onClick={() => handleEditOrganization(org)}
                        className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                        title="Edit organization"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Organization Brands */}
                {orgBrands.length > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 ml-13">
                    {orgBrands.map((brand) => (
                      <div
                        key={brand.id}
                        className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold">
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
                              {brand.url && (
                                <a 
                                  href={brand.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-xs text-blue-400 hover:text-blue-300"
                                >
                                  {brand.url}
                                </a>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleEditBrand(brand)}
                              className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                              title="Edit brand"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteBrand(brand)}
                              className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-red-400"
                              title="Delete brand"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
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

                        {/* Actions */}
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
                  <div className="ml-13 p-6 text-center border border-dashed border-white/20 rounded-lg">
                    <p className="text-gray-400 mb-3">No brands in this organization yet</p>
                    <button
                      onClick={() => {
                        setFormData({ name: '', description: '', url: '', organization_id: org.id });
                        setShowCreateModal(true);
                      }}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-opacity"
                    >
                      Create First Brand
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Personal Brands (No Organization) */}
      {(() => {
        const personalBrands = brands.filter(brand => !brand.organization_id);
        if (personalBrands.length > 0) {
          return (
            <div className={`bg-white/5 border border-white/10 rounded-lg p-6 ${organizations.length > 0 ? 'mt-8' : ''}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold">Personal Brands</h2>
                  <p className="text-sm text-gray-400">Brands not associated with any organization</p>
                </div>
                <button
                  onClick={() => {
                    setFormData({ name: '', description: '', url: '', organization_id: null });
                    setShowCreateModal(true);
                  }}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-opacity"
                >
                  Add Personal Brand
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {personalBrands.map((brand) => (
                  <div
                    key={brand.id}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold">
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
                          {brand.url && (
                            <a 
                              href={brand.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-blue-400 hover:text-blue-300"
                            >
                              {brand.url}
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleEditBrand(brand)}
                          className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                          title="Edit brand"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteBrand(brand)}
                          className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-red-400"
                          title="Delete brand"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
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

                    {/* Actions */}
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
            </div>
          );
        }
        return null;
      })()}

      {/* Empty State - when no brands and no organizations */}
      {brands.length === 0 && organizations.length === 0 && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
            <Plus className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-bold mb-2">Get Started</h3>
          <p className="text-gray-400 mb-6">
            Create an organization and your first brand to start managing your social media
          </p>
          <div className="flex gap-3 justify-center">
            <button 
              onClick={() => setShowCreateOrgModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Create Organization
            </button>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-opacity"
            >
              Create Personal Brand
            </button>
          </div>
        </div>
      )}

      {/* Create Brand Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Create New Brand</h2>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateBrand} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Brand Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter brand name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-20 resize-none"
                  placeholder="Brief description of your brand"
                />
              </div>

              {organizations.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-2">Organization (Optional)</label>
                  <select
                    value={formData.organization_id || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      organization_id: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">No Organization</option>
                    {organizations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name} {org.is_admin ? "(Admin)" : "(Member)"}
                      </option>
                    ))}
                  </select>
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-xs text-gray-400">
                      Select an organization to enable default brand selection
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateModal(false);
                        setShowCreateOrgModal(true);
                      }}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      + Create New Organization
                    </button>
                  </div>
                </div>
              )}

              {organizations.length === 0 && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-blue-400 mt-0.5">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-blue-400 mb-1">No Organizations Found</p>
                      <p className="text-xs text-blue-300 mb-2">
                        Create an organization to enable team collaboration and default brand selection.
                      </p>
                      <button
                        type="button"
                        onClick={() => {
                          setShowCreateModal(false);
                          setShowCreateOrgModal(true);
                        }}
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg transition-colors"
                      >
                        Create Organization
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Website URL *</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="https://yourbrand.com"
                  required
                />
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
                  {createLoading ? "Creating..." : "Create Brand"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Brand Modal */}
      {showEditModal && editingBrand && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Edit Brand</h2>
              <button 
                onClick={() => {
                  setShowEditModal(false);
                  setEditingBrand(null);
                  setFormData({ name: '', description: '', url: '', organization_id: null });
                }}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateBrand} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Brand Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter brand name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-20 resize-none"
                  placeholder="Brief description of your brand"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Website URL *</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="https://yourbrand.com"
                  required
                />
              </div>

              {organizations.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-2">Organization (Optional)</label>
                  <select
                    value={formData.organization_id || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      organization_id: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">No Organization</option>
                    {organizations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name} {org.is_admin ? "(Admin)" : "(Member)"}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingBrand(null);
                    setFormData({ name: '', description: '', url: '', organization_id: null });
                  }}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 disabled:opacity-50 py-2 px-4 rounded-lg transition-opacity font-medium"
                >
                  {createLoading ? "Updating..." : "Update Brand"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Organization Modal */}
      {showCreateOrgModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Create New Organization</h2>
              <button 
                onClick={() => setShowCreateOrgModal(false)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateOrganization} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Organization Name *</label>
                <input
                  type="text"
                  value={orgFormData.name}
                  onChange={(e) => setOrgFormData({ ...orgFormData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter organization name"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">
                  You will be the admin of this organization
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateOrgModal(false)}
                  className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createOrgLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-2 px-4 rounded-lg transition-colors font-medium"
                >
                  {createOrgLoading ? "Creating..." : "Create Organization"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Brand Confirmation Modal */}
      {showDeleteModal && deletingBrand && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-red-400">Delete Brand</h2>
              <button 
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingBrand(null);
                }}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-gray-300 mb-2">
                Are you sure you want to delete the brand "{deletingBrand.name}"?
              </p>
              <p className="text-sm text-red-400">
                This action cannot be undone. All associated data will be permanently deleted.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingBrand(null);
                }}
                className="flex-1 py-2 px-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteBrand}
                disabled={deleteLoading}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 py-2 px-4 rounded-lg transition-colors font-medium"
              >
                {deleteLoading ? "Deleting..." : "Delete Brand"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
