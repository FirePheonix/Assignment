"use client";

import { Plus, Calendar, Tag, AlertCircle, Loader2, CheckCircle, DollarSign, Gift } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  createTask, 
  CreateTaskData, 
  TaskCategory, 
  TaskGenre, 
  IncentiveType,
  CATEGORY_LABELS,
  GENRE_LABELS,
  INCENTIVE_LABELS
} from "@/lib/api/tasks";
import { getCurrentUser } from "@/lib/auth";

export default function CreateTaskPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<CreateTaskData>({
    title: "",
    description: "",
    category: "POST" as TaskCategory,
    genre: "OTHER" as TaskGenre,
    incentive_type: "BARTER" as IncentiveType,
    barter_details: "",
    pay_amount: undefined,
    commission_percentage: undefined,
    gift_card_amount: undefined,
    experience_details: "",
    deadline: "",
  });

  useEffect(() => {
    // Auth already checked by layout
    setCheckingAuth(false);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Prepare data based on incentive type
    const taskData: CreateTaskData = {
      title: formData.title,
      description: formData.description,
      category: formData.category,
      genre: formData.genre,
      incentive_type: formData.incentive_type,
      deadline: formData.deadline || undefined,
    };

    // Add incentive-specific fields
    if (formData.incentive_type === 'BARTER') {
      taskData.barter_details = formData.barter_details;
    } else if (formData.incentive_type === 'PAY') {
      taskData.pay_amount = formData.pay_amount;
    } else if (formData.incentive_type === 'COMMISSION') {
      taskData.commission_percentage = formData.commission_percentage;
    } else if (formData.incentive_type === 'GIFT_CARD') {
      taskData.gift_card_amount = formData.gift_card_amount;
    } else if (formData.incentive_type === 'EXPERIENCE') {
      taskData.experience_details = formData.experience_details;
    }

    const { data, error: apiError } = await createTask(taskData);

    if (apiError) {
      setError(apiError);
      setLoading(false);
      return;
    }

    if (data) {
      setSuccess(true);
      setTimeout(() => {
        router.push(`/dashboard/tasks/${data.id}`);
      }, 1500);
    }
  }

  if (checkingAuth) {
    return (
      <div className="p-8 bg-black min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (success) {
    return (
      <div className="p-8 bg-black min-h-screen flex items-center justify-center">
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-8 text-center max-w-md">
          <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-white mb-2">Task Created!</h3>
          <p className="text-gray-400">Redirecting to task details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">Create New Task</h1>
        <p className="text-gray-400">Post a collaboration opportunity for creators</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-400 font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Form */}
      <div className="max-w-3xl">
        <form onSubmit={handleSubmit} className="bg-[#1a1a1a] border border-white/10 rounded-xl p-8">
          <div className="space-y-6">
            {/* Task Title */}
            <div>
              <label className="flex text-sm font-medium text-gray-400 mb-2">
                Task Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="e.g., Create Instagram Reel for Product Launch"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="flex text-sm font-medium text-gray-400 mb-2">
                Description *
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Describe what you need the creator to do..."
                required
              />
            </div>

            {/* Category & Genre */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Content Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as TaskCategory })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Industry Genre *
                </label>
                <select
                  value={formData.genre}
                  onChange={(e) => setFormData({ ...formData, genre: e.target.value as TaskGenre })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  {Object.entries(GENRE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Incentive Type */}
            <div>
              <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                <Gift className="w-4 h-4" />
                Compensation Type *
              </label>
              <select
                value={formData.incentive_type}
                onChange={(e) => setFormData({ ...formData, incentive_type: e.target.value as IncentiveType })}
                className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
              >
                {Object.entries(INCENTIVE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            {/* Conditional Incentive Fields */}
            {formData.incentive_type === 'BARTER' && (
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2">
                  Product/Service Details *
                </label>
                <textarea
                  rows={3}
                  value={formData.barter_details}
                  onChange={(e) => setFormData({ ...formData, barter_details: e.target.value })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Describe what product/service you're offering in exchange..."
                  required
                />
              </div>
            )}

            {formData.incentive_type === 'PAY' && (
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  Payment Amount ($) *
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.pay_amount || ''}
                  onChange={(e) => setFormData({ ...formData, pay_amount: parseFloat(e.target.value) || undefined })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="0.00"
                  required
                />
              </div>
            )}

            {formData.incentive_type === 'COMMISSION' && (
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2">
                  Commission Percentage (%) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={formData.commission_percentage || ''}
                  onChange={(e) => setFormData({ ...formData, commission_percentage: parseFloat(e.target.value) || undefined })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="0.0"
                  required
                />
              </div>
            )}

            {formData.incentive_type === 'GIFT_CARD' && (
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                  <Gift className="w-4 h-4" />
                  Gift Card Amount ($) *
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.gift_card_amount || ''}
                  onChange={(e) => setFormData({ ...formData, gift_card_amount: parseFloat(e.target.value) || undefined })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="0.00"
                  required
                />
              </div>
            )}

            {formData.incentive_type === 'EXPERIENCE' && (
              <div>
                <label className="flex text-sm font-medium text-gray-400 mb-2">
                  Experience/Event Details *
                </label>
                <textarea
                  rows={3}
                  value={formData.experience_details}
                  onChange={(e) => setFormData({ ...formData, experience_details: e.target.value })}
                  className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Describe the experience or event access you're offering..."
                  required
                />
              </div>
            )}

            {/* Deadline */}
            <div>
              <label className="flex text-sm font-medium text-gray-400 mb-2 items-center gap-2">
                <Calendar className="w-4 h-4" />
                Deadline (Optional)
              </label>
              <input
                type="datetime-local"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                className="w-full p-3 bg-black border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-6 border-t border-white/10">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-medium transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Task
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => router.back()}
                className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-lg font-medium transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>

        {/* Tips */}
        <div className="mt-6 bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
          <h4 className="text-blue-400 font-medium mb-2">💡 Tips for Creating Tasks</h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>• Be specific about deliverables and expectations</li>
            <li>• Choose appropriate compensation based on the work required</li>
            <li>• Set realistic deadlines to attract quality creators</li>
            <li>• Provide detailed descriptions to reduce back-and-forth</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
