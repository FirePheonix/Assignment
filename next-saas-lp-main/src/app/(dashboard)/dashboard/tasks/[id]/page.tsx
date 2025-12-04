"use client";

import { 
  Calendar, 
  Tag, 
  AlertCircle, 
  Loader2, 
  CheckCircle, 
  DollarSign, 
  User,
  Clock,
  ChevronLeft,
  Send,
  CheckSquare,
  XCircle
} from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { 
  getTask,
  applyToTask,
  getTaskApplications,
  updateApplicationStatus,
  Task,
  TaskApplication,
  ApplicationStatus,
  CATEGORY_LABELS,
  GENRE_LABELS,
  INCENTIVE_LABELS
} from "@/lib/api/tasks";
import { getCurrentUser, User as AuthUser } from "@/lib/auth";

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.id ? parseInt(params.id as string) : null;
  
  const [user, setUser] = useState<AuthUser | null>(null);
  const [task, setTask] = useState<Task | null>(null);
  const [applications, setApplications] = useState<TaskApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [applicationMessage, setApplicationMessage] = useState("");
  const [showApplicationForm, setShowApplicationForm] = useState(false);

  useEffect(() => {
    if (taskId) {
      loadData();
    }
  }, [taskId]);

  async function loadData() {
    setLoading(true);
    setError(null);
    
    // Get current user
    const currentUser = await getCurrentUser();
    setUser(currentUser);

    if (!taskId) {
      setError("Invalid task ID");
      setLoading(false);
      return;
    }

    // Load task details
    const { data: taskData, error: taskError } = await getTask(taskId);
    
    if (taskError) {
      setError(taskError);
      setLoading(false);
      return;
    }

    if (taskData) {
      setTask(taskData);
      
      // If user is the task owner, load applications
      if (currentUser && taskData.brand === currentUser.id) {
        const { data: appsData } = await getTaskApplications(taskId);
        if (appsData) {
          setApplications(appsData.applications);
        }
      }
    }

    setLoading(false);
  }

  async function handleApply(e: React.FormEvent) {
    e.preventDefault();
    if (!taskId) return;
    
    setApplyLoading(true);
    setError(null);

    const { data, error: apiError } = await applyToTask(taskId, applicationMessage);

    if (apiError) {
      setError(apiError);
      setApplyLoading(false);
      return;
    }

    if (data) {
      setApplySuccess(true);
      setShowApplicationForm(false);
      setApplicationMessage("");
      // Reload task to update application status
      setTimeout(() => {
        loadData();
        setApplySuccess(false);
      }, 2000);
    }
    
    setApplyLoading(false);
  }

  async function handleUpdateApplicationStatus(applicationId: number, status: ApplicationStatus) {
    const { data, error: apiError } = await updateApplicationStatus(applicationId, status);
    
    if (apiError) {
      setError(apiError);
      return;
    }

    if (data) {
      // Reload applications
      loadData();
    }
  }

  const formatDeadline = (deadline?: string) => {
    if (!deadline) return 'No deadline';
    const date = new Date(deadline);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Overdue';
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    return `${date.toLocaleDateString()} (${diffDays} days)`;
  };

  const getIncentiveDisplay = (task: Task) => {
    if (task.incentive_type === 'PAY' && task.pay_amount) {
      return `$${task.pay_amount}`;
    } else if (task.incentive_type === 'COMMISSION' && task.commission_percentage) {
      return `${task.commission_percentage}% Commission`;
    } else if (task.incentive_type === 'GIFT_CARD' && task.gift_card_amount) {
      return `$${task.gift_card_amount} Gift Card`;
    }
    return INCENTIVE_LABELS[task.incentive_type];
  };

  const isOwner = user && task && task.brand === user.id;
  const hasApplied = task?.user_has_applied;

  if (loading) {
    return (
      <div className="p-8 bg-black min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading task details...</p>
        </div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="p-8 bg-black min-h-screen">
        <div className="background-pattern-blue" />
        <div className="max-w-4xl mx-auto relative z-10">
          <button
            onClick={() => router.push('/dashboard/tasks')}
            className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            Back to Tasks
          </button>
          
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-8 text-center">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-white mb-2">Task Not Found</h3>
            <p className="text-gray-400 mb-6">{error || "The task you're looking for doesn't exist."}</p>
            <button
              onClick={() => router.push('/dashboard/tasks')}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              View All Tasks
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-black min-h-screen">
      {/* Background Pattern */}
      <div className="background-pattern-blue" />

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Back Button */}
        <button
          onClick={() => router.push('/dashboard/tasks')}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
          Back to Tasks
        </button>

        {/* Success Message */}
        {applySuccess && (
          <div className="mb-6 bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <p className="text-green-400 font-medium">Application submitted successfully!</p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && !applySuccess && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-400 font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* Task Details Card */}
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-8 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-white mb-3">{task.title}</h1>
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span>Posted by {task.brand_username}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(task.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
            
            {!task.is_active && (
              <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-lg">
                <span className="text-red-400 text-sm font-medium">Inactive</span>
              </div>
            )}
          </div>

          {/* Task Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-black/50 border border-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <Tag className="w-4 h-4" />
                <span className="text-sm">Category</span>
              </div>
              <p className="text-white font-medium">{CATEGORY_LABELS[task.category]}</p>
            </div>

            <div className="bg-black/50 border border-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <Tag className="w-4 h-4" />
                <span className="text-sm">Genre</span>
              </div>
              <p className="text-white font-medium">{GENRE_LABELS[task.genre]}</p>
            </div>

            <div className="bg-black/50 border border-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <DollarSign className="w-4 h-4" />
                <span className="text-sm">Incentive</span>
              </div>
              <p className="text-white font-medium">{getIncentiveDisplay(task)}</p>
            </div>
          </div>

          {/* Deadline */}
          {task.deadline && (
            <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-purple-400" />
                <div>
                  <p className="text-sm text-gray-400">Deadline</p>
                  <p className="text-white font-medium">{formatDeadline(task.deadline)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Description */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">Description</h3>
            <p className="text-gray-300 whitespace-pre-wrap">{task.description}</p>
          </div>

          {/* Incentive Details */}
          {task.incentive_type === 'BARTER' && task.barter_details && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3">Barter Details</h3>
              <p className="text-gray-300">{task.barter_details}</p>
            </div>
          )}

          {task.incentive_type === 'EXPERIENCE' && task.experience_details && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3">Experience Details</h3>
              <p className="text-gray-300">{task.experience_details}</p>
            </div>
          )}

          {/* Application Stats */}
          <div className="flex items-center gap-6 pt-6 border-t border-white/10">
            <div>
              <p className="text-sm text-gray-400">Total Applications</p>
              <p className="text-2xl font-bold text-white">{task.application_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Accepted</p>
              <p className="text-2xl font-bold text-green-400">{task.accepted_applications_count}</p>
            </div>
          </div>
        </div>

        {/* Apply Section (Non-owners only) */}
        {!isOwner && user && task.is_active && (
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-8 mb-6">
            <h3 className="text-xl font-bold text-white mb-4">Apply for This Task</h3>
            
            {hasApplied ? (
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <p className="text-green-400 font-medium">You have already applied for this task</p>
                </div>
              </div>
            ) : showApplicationForm ? (
              <form onSubmit={handleApply}>
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-400 mb-2 block">
                    Application Message
                  </label>
                  <textarea
                    value={applicationMessage}
                    onChange={(e) => setApplicationMessage(e.target.value)}
                    className="w-full p-3 bg-black border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 min-h-[120px]"
                    placeholder="Explain why you're a good fit for this task..."
                    required
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={applyLoading}
                    className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 text-white rounded-lg transition-colors"
                  >
                    {applyLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        Submit Application
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowApplicationForm(false)}
                    className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setShowApplicationForm(true)}
                className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <Send className="w-5 h-5" />
                Apply Now
              </button>
            )}
          </div>
        )}

        {/* Applications List (Owners only) */}
        {isOwner && applications.length > 0 && (
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-8">
            <h3 className="text-xl font-bold text-white mb-6">Applications ({applications.length})</h3>
            
            <div className="space-y-4">
              {applications.map((app) => (
                <div 
                  key={app.id}
                  className="bg-black/50 border border-white/5 rounded-lg p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <p className="text-white font-semibold">{app.creator_username}</p>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          app.status === 'ACCEPTED' ? 'bg-green-500/10 text-green-400 border border-green-500/30' :
                          app.status === 'REJECTED' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                          'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                        }`}>
                          {app.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400">{app.creator_email}</p>
                      <p className="text-sm text-gray-500">
                        Applied {new Date(app.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <p className="text-gray-300 mb-4">{app.message}</p>

                  {app.status === 'PENDING' && (
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleUpdateApplicationStatus(app.id, 'ACCEPTED')}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm"
                      >
                        <CheckSquare className="w-4 h-4" />
                        Accept
                      </button>
                      <button
                        onClick={() => handleUpdateApplicationStatus(app.id, 'REJECTED')}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-sm"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {isOwner && applications.length === 0 && (
          <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-8 text-center">
            <p className="text-gray-400">No applications yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
