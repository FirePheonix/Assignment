"use client";

import { CheckSquare, Filter, Calendar, User, Loader2, AlertCircle, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { 
  getTasks, 
  Task, 
  TaskCategory, 
  TaskGenre, 
  IncentiveType,
  CATEGORY_LABELS,
  GENRE_LABELS,
  INCENTIVE_LABELS
} from "@/lib/api/tasks";
import { getCurrentUser } from "@/lib/auth";

export default function AllTasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<TaskCategory | "">("");
  const [genreFilter, setGenreFilter] = useState<TaskGenre | "">("");
  const [incentiveFilter, setIncentiveFilter] = useState<IncentiveType | "">("");
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    checkAuthAndLoad();
  }, []);

  useEffect(() => {
    if (authChecked) {
      loadTasks();
    }
  }, [categoryFilter, genreFilter, incentiveFilter, authChecked]);

  async function checkAuthAndLoad() {
    // Auth already checked by layout, just proceed
    setAuthChecked(true);
  }

  async function loadTasks() {
    setLoading(true);
    setError(null);

    const params: any = { page_size: 100 };
    if (categoryFilter) params.category = categoryFilter;
    if (genreFilter) params.genre = genreFilter;
    if (incentiveFilter) params.incentive_type = incentiveFilter;

    const { data, error: tasksError } = await getTasks(params);

    if (tasksError) {
      setError(tasksError);
      setLoading(false);
      return;
    }

    if (data) {
      setTasks(data.tasks);
    }

    setLoading(false);
  }

  const filteredTasks = tasks.filter(task => 
    searchQuery === "" || 
    task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.brand_username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const taskStats = {
    total: filteredTasks.length,
    active: filteredTasks.filter(t => t.is_active).length,
    withApplications: filteredTasks.filter(t => t.application_count > 0).length,
  };

  const formatDeadline = (deadline?: string) => {
    if (!deadline) return 'No deadline';
    return new Date(deadline).toLocaleDateString();
  };

  const getIncentiveDisplay = (task: Task) => {
    if (task.incentive_type === 'PAY' && task.pay_amount) {
      return `$${task.pay_amount}`;
    } else if (task.incentive_type === 'COMMISSION' && task.commission_percentage) {
      return `${task.commission_percentage}%`;
    } else if (task.incentive_type === 'GIFT_CARD' && task.gift_card_amount) {
      return `$${task.gift_card_amount}`;
    }
    return INCENTIVE_LABELS[task.incentive_type].substring(0, 15);
  };

  if (loading) {
    return (
      <div className="p-8 bg-black min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading tasks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-black min-h-screen">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Error Loading Tasks</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={loadTasks}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-black min-h-screen relative">
      {/* Background Pattern - Blue waves at top */}
      <div className="absolute top-0 left-0 right-0 h-[300px] overflow-hidden pointer-events-none">
        <img 
          src="/images/background-pattern-blue.png" 
          alt="" 
          className="w-full h-full object-cover opacity-60 rounded-3xl"
        />
      </div>

      {/* Header */}
      <div className="mb-6 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-2">All Tasks</h1>
        <p className="text-gray-400">Browse all available collaboration tasks</p>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tasks..."
            className="w-full pl-10 pr-4 py-3 bg-[#1a1a1a] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as TaskCategory | "")}
          className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Categories</option>
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <select
          value={genreFilter}
          onChange={(e) => setGenreFilter(e.target.value as TaskGenre | "")}
          className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Genres</option>
          {Object.entries(GENRE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <select
          value={incentiveFilter}
          onChange={(e) => setIncentiveFilter(e.target.value as IncentiveType | "")}
          className="bg-[#1a1a1a] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Compensation</option>
          {Object.entries(INCENTIVE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-4">
          <p className="text-sm text-gray-400">Total Tasks</p>
          <p className="text-2xl font-bold text-white mt-1">{taskStats.total}</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-4">
          <p className="text-sm text-gray-400">Active</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">{taskStats.active}</p>
        </div>
        <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-4">
          <p className="text-sm text-gray-400">With Applicants</p>
          <p className="text-2xl font-bold text-green-400 mt-1">{taskStats.withApplications}</p>
        </div>
      </div>

      {/* Tasks Table */}
      {filteredTasks.length === 0 ? (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
          <CheckSquare className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">No Tasks Found</h3>
          <p className="text-gray-400">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-black border-b border-white/10 text-sm font-medium text-gray-400">
            <div className="col-span-4">Task</div>
            <div className="col-span-2">Category</div>
            <div className="col-span-2">Compensation</div>
            <div className="col-span-2">Deadline</div>
            <div className="col-span-2">Brand / Apps</div>
          </div>

          {/* Table Body */}
          <div className="divide-y divide-white/10">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-white/5 transition cursor-pointer"
                onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
              >
                {/* Task Name */}
                <div className="col-span-4 flex flex-col justify-center">
                  <p className="font-medium text-white line-clamp-1">{task.title}</p>
                  <p className="text-sm text-gray-400 line-clamp-1">{task.description}</p>
                </div>

                {/* Category */}
                <div className="col-span-2 flex items-center">
                  <span className="bg-blue-500/20 text-blue-400 text-xs px-3 py-1 rounded">
                    {CATEGORY_LABELS[task.category]}
                  </span>
                </div>

                {/* Compensation */}
                <div className="col-span-2 flex items-center">
                  <span className="bg-green-500/20 text-green-400 text-xs px-3 py-1 rounded">
                    {getIncentiveDisplay(task)}
                  </span>
                </div>

                {/* Deadline */}
                <div className="col-span-2 flex items-center">
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDeadline(task.deadline)}</span>
                  </div>
                </div>

                {/* Brand / Applicants */}
                <div className="col-span-2 flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <User className="w-3 h-3" />
                    <span className="truncate">{task.brand_username}</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {task.application_count} applicant{task.application_count !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-black border-t border-white/10 flex items-center justify-between">
            <p className="text-sm text-gray-400">
              Showing {filteredTasks.length} task{filteredTasks.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
