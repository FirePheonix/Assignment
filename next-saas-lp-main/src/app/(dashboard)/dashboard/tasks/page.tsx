"use client";

import { CheckSquare, Calendar, Plus, AlertCircle, Clock, User, Loader2, MessageSquare, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getTasks, getMyApplications, Task, TaskApplication, CATEGORY_LABELS, INCENTIVE_LABELS } from "@/lib/api/tasks";
import { getCurrentUser, User as AuthUser } from "@/lib/auth";

type ViewMode = 'overview' | 'board' | 'kanban' | 'timeline' | 'table';

export default function TasksDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [applications, setApplications] = useState<TaskApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'applied' | 'my-tasks'>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Start week on Monday
    const monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    monday.setHours(0, 0, 0, 0);
    return monday;
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    
    // Get current user (auth already checked by layout)
    const currentUser = await getCurrentUser();
    setUser(currentUser);

    // Load tasks
    const { data: tasksData, error: tasksError } = await getTasks({ page_size: 50 });
    
    if (tasksError) {
      setError(tasksError);
      setLoading(false);
      return;
    }

    if (tasksData) {
      setTasks(tasksData.tasks);
    }

    // Load user's applications if authenticated
    if (currentUser) {
      const { data: appsData } = await getMyApplications();
      if (appsData) {
        setApplications(appsData.applications);
      }
    }

    setLoading(false);
  }

  const getFilteredTasks = () => {
    if (activeFilter === 'applied') {
      const appliedTaskIds = new Set(applications.map(app => app.task));
      return tasks.filter(task => appliedTaskIds.has(task.id));
    } else if (activeFilter === 'my-tasks') {
      return tasks.filter(task => task.brand === user?.id);
    }
    return tasks;
  };

  const filteredTasks = getFilteredTasks();

  // Generate week days for timeline view
  const getWeekDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(currentWeekStart);
      date.setDate(currentWeekStart.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const weekDays = getWeekDays();

  // Group tasks by date
  const getTasksForDate = (date: Date) => {
    return filteredTasks.filter(task => {
      if (!task.deadline) return false;
      const taskDate = new Date(task.deadline);
      return (
        taskDate.getFullYear() === date.getFullYear() &&
        taskDate.getMonth() === date.getMonth() &&
        taskDate.getDate() === date.getDate()
      );
    });
  };

  const goToPreviousWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() - 7);
    setCurrentWeekStart(newDate);
  };

  const goToNextWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() + 7);
    setCurrentWeekStart(newDate);
  };

  const goToToday = () => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    const monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    monday.setHours(0, 0, 0, 0);
    setCurrentWeekStart(monday);
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    );
  };

  const getTaskColor = (task: Task) => {
    const colors = [
      'border-l-green-500',
      'border-l-orange-500',
      'border-l-blue-500',
      'border-l-purple-500',
      'border-l-pink-500',
      'border-l-yellow-500',
    ];
    return colors[task.id % colors.length];
  };
  
  const taskStats = {
    total: tasks.length,
    active: tasks.filter(t => t.is_active).length,
    myTasks: user ? tasks.filter(t => t.brand === user.id).length : 0,
    applied: applications.length,
  };

  const formatDeadline = (deadline?: string) => {
    if (!deadline) return 'No deadline';
    const date = new Date(deadline);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Overdue';
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    return date.toLocaleDateString();
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
            onClick={loadData}
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
          src="/images/background-pattern-blue.svg" 
          alt="" 
          className="w-full h-full object-cover opacity-60 rounded-3xl"
        />
      </div>

      {/* Header */}
      <div className="mb-8 flex items-start justify-between relative z-10">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Available Tasks</h1>
          <p className="text-gray-400 text-sm">Discover and manage brand collaboration opportunities</p>
        </div>
        {user && (
          <button
            onClick={() => router.push('/dashboard/tasks/create')}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Task
          </button>
        )}
      </div>

      {/* View Tabs */}
      <div className="mb-6 border-b border-white/10">
        <div className="flex gap-8">
          <button
            onClick={() => setViewMode('overview')}
            className={`pb-3 px-1 font-medium transition border-b-2 ${
              viewMode === 'overview'
                ? 'text-white border-purple-600'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setViewMode('board')}
            className={`pb-3 px-1 font-medium transition border-b-2 ${
              viewMode === 'board'
                ? 'text-white border-purple-600'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            Board
          </button>
          <button
            onClick={() => setViewMode('kanban')}
            className={`pb-3 px-1 font-medium transition border-b-2 ${
              viewMode === 'kanban'
                ? 'text-white border-purple-600'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            Kanban
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`pb-3 px-1 font-medium transition border-b-2 ${
              viewMode === 'timeline'
                ? 'text-white border-purple-600'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            Timeline
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`pb-3 px-1 font-medium transition border-b-2 ${
              viewMode === 'table'
                ? 'text-white border-purple-600'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            Table
          </button>
        </div>
      </div>

      {/* Week Navigation - Only in timeline view */}
      {viewMode === 'timeline' && (
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={goToPreviousWeek}
              className="p-2 hover:bg-white/5 rounded-lg transition"
            >
              <ChevronLeft className="w-5 h-5 text-gray-400" />
            </button>
            <button
              onClick={goToNextWeek}
              className="p-2 hover:bg-white/5 rounded-lg transition"
            >
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>
            <button
              onClick={goToToday}
              className="px-4 py-2 text-sm font-medium text-gray-300 hover:bg-white/5 rounded-lg transition"
            >
              Today
            </button>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeFilter === 'all'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/5 hover:bg-white/10 text-gray-400'
              }`}
            >
              All
            </button>
            {user && (
              <>
                <button
                  onClick={() => setActiveFilter('applied')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    activeFilter === 'applied'
                      ? 'bg-purple-600 text-white'
                      : 'bg-white/5 hover:bg-white/10 text-gray-400'
                  }`}
                >
                  Applied
                </button>
                <button
                  onClick={() => setActiveFilter('my-tasks')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    activeFilter === 'my-tasks'
                      ? 'bg-purple-600 text-white'
                      : 'bg-white/5 hover:bg-white/10 text-gray-400'
                  }`}
                >
                  My Tasks
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="bg-black">
          {/* Week Header */}
          <div className="grid grid-cols-7 gap-4 mb-4">
            {weekDays.map((date, index) => {
              const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
              const dayNum = date.getDate();
              const monthName = date.toLocaleDateString('en-US', { month: 'short' });
              const isTodayDate = isToday(date);
              
              return (
                <div key={index} className="text-center">
                  <div className={`inline-flex flex-col items-center justify-center rounded-lg p-3 transition ${
                    isTodayDate ? 'bg-purple-600 text-white' : 'text-gray-400 bg-white/5'
                  }`}>
                    <span className="text-sm font-medium">{dayName}</span>
                    <span className="text-xs opacity-75">{monthName}, {String(dayNum).padStart(2, '0')}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Timeline Grid */}
          <div className="grid grid-cols-7 gap-4 relative">
            {/* Vertical lines connecting days */}
            <div className="absolute inset-0 grid grid-cols-7 gap-4 pointer-events-none">
              {weekDays.map((_, index) => (
                <div key={index} className="border-l border-white/10" />
              ))}
            </div>

            {/* Task Cards */}
            {weekDays.map((date, dayIndex) => {
              const tasksForDay = getTasksForDate(date);
              
              return (
                <div key={dayIndex} className="relative min-h-[400px] pt-4">
                  <div className="space-y-3">
                    {tasksForDay.map((task) => {
                      const hasApplied = applications.some(app => app.task === task.id);
                      const isOwner = user && task.brand === user.id;
                      
                      return (
                        <div
                          key={task.id}
                          className={`bg-[#1a1a1a] border-l-4 ${getTaskColor(task)} rounded-lg hover:bg-[#202020] transition cursor-pointer p-4 border border-white/10`}
                          onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                        >
                          <h4 className="font-semibold text-white text-sm mb-2 line-clamp-2">
                            {task.title}
                          </h4>
                          <p className="text-xs text-gray-400 mb-3 line-clamp-2">
                            {task.description}
                          </p>
                          
                          {/* Avatar Group */}
                          <div className="flex items-center gap-2 mb-3">
                            <div className="flex -space-x-2">
                              {[...Array(Math.min(3, task.application_count || 1))].map((_, i) => (
                                <div
                                  key={i}
                                  className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 border-2 border-[#1a1a1a] flex items-center justify-center text-[10px] text-white font-medium"
                                >
                                  {String.fromCharCode(65 + i)}
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Stats */}
                          <div className="flex items-center gap-3 text-xs text-gray-400">
                            <div className="flex items-center gap-1">
                              <MessageSquare className="w-3 h-3" />
                              <span>{task.application_count || 0}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <CheckSquare className="w-3 h-3" />
                              <span>{task.accepted_applications_count || 0}</span>
                            </div>
                          </div>

                          {/* Tags */}
                          {(hasApplied || isOwner) && (
                            <div className="flex gap-1 mt-2">
                              {hasApplied && (
                                <span className="bg-green-500/20 text-green-400 text-[10px] px-2 py-0.5 rounded">
                                  Applied
                                </span>
                              )}
                              {isOwner && (
                                <span className="bg-yellow-500/20 text-yellow-400 text-[10px] px-2 py-0.5 rounded">
                                  Mine
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Empty State */}
          {filteredTasks.filter(t => t.deadline).length === 0 && (
            <div className="text-center py-16">
              <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No Tasks Scheduled</h3>
              <p className="text-gray-400 mb-6">
                {activeFilter === 'applied'
                  ? "You haven't applied to any tasks yet."
                  : activeFilter === 'my-tasks'
                  ? "You haven't created any tasks with deadlines yet."
                  : 'No tasks with deadlines available.'}
              </p>
              {user && (
                <button
                  onClick={() => router.push('/dashboard/tasks/create')}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Task
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Kanban View */}
      {viewMode === 'kanban' && (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {/* Open Column */}
          <div className="flex-shrink-0 w-80">
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  Open
                </h3>
                <span className="text-gray-400 text-sm">
                  {filteredTasks.filter(t => t.is_active && !applications.some(app => app.task === t.id)).length}
                </span>
              </div>
              <div className="space-y-3">
                {filteredTasks
                  .filter(t => t.is_active && !applications.some(app => app.task === t.id) && t.brand !== user?.id)
                  .map((task) => (
                    <div
                      key={task.id}
                      className="bg-black/50 border border-white/5 rounded-lg p-4 cursor-pointer hover:border-purple-500/50 transition"
                      onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                    >
                      <h4 className="text-white font-medium text-sm mb-2 line-clamp-2">{task.title}</h4>
                      <p className="text-gray-400 text-xs mb-3 line-clamp-2">{task.description}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">{CATEGORY_LABELS[task.category]}</span>
                        <div className="flex items-center gap-1 text-gray-400">
                          <MessageSquare className="w-3 h-3" />
                          <span className="text-xs">{task.application_count}</span>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Applied Column */}
          <div className="flex-shrink-0 w-80">
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                  Applied
                </h3>
                <span className="text-gray-400 text-sm">
                  {applications.filter(app => app.status === 'PENDING').length}
                </span>
              </div>
              <div className="space-y-3">
                {applications
                  .filter(app => app.status === 'PENDING')
                  .map((app) => {
                    const task = tasks.find(t => t.id === app.task);
                    if (!task) return null;
                    return (
                      <div
                        key={app.id}
                        className="bg-black/50 border border-white/5 rounded-lg p-4 cursor-pointer hover:border-purple-500/50 transition"
                        onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                      >
                        <h4 className="text-white font-medium text-sm mb-2 line-clamp-2">{task.title}</h4>
                        <p className="text-gray-400 text-xs mb-3 line-clamp-2">{task.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-yellow-400">Pending Review</span>
                          <span className="text-xs text-gray-500">{new Date(app.applied_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Accepted Column */}
          <div className="flex-shrink-0 w-80">
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  Accepted
                </h3>
                <span className="text-gray-400 text-sm">
                  {applications.filter(app => app.status === 'ACCEPTED').length}
                </span>
              </div>
              <div className="space-y-3">
                {applications
                  .filter(app => app.status === 'ACCEPTED')
                  .map((app) => {
                    const task = tasks.find(t => t.id === app.task);
                    if (!task) return null;
                    return (
                      <div
                        key={app.id}
                        className="bg-black/50 border border-white/5 rounded-lg p-4 cursor-pointer hover:border-purple-500/50 transition"
                        onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                      >
                        <h4 className="text-white font-medium text-sm mb-2 line-clamp-2">{task.title}</h4>
                        <p className="text-gray-400 text-xs mb-3 line-clamp-2">{task.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-green-400">Accepted</span>
                          <span className="text-xs text-gray-500">{formatDeadline(task.deadline)}</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* My Tasks Column */}
          {user && (
            <div className="flex-shrink-0 w-80">
              <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-semibold flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                    My Tasks
                  </h3>
                  <span className="text-gray-400 text-sm">
                    {filteredTasks.filter(t => t.brand === user.id).length}
                  </span>
                </div>
                <div className="space-y-3">
                  {filteredTasks
                    .filter(t => t.brand === user.id)
                    .map((task) => (
                      <div
                        key={task.id}
                        className="bg-black/50 border border-white/5 rounded-lg p-4 cursor-pointer hover:border-purple-500/50 transition"
                        onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                      >
                        <h4 className="text-white font-medium text-sm mb-2 line-clamp-2">{task.title}</h4>
                        <p className="text-gray-400 text-xs mb-3 line-clamp-2">{task.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-purple-400">{task.application_count} applicants</span>
                          <span className={`text-xs ${task.is_active ? 'text-green-400' : 'text-red-400'}`}>
                            {task.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Board View */}
      {viewMode === 'board' && (
        <div className="space-y-4">
          {filteredTasks.map((task) => {
            const hasApplied = applications.some(app => app.task === task.id);
            const isOwner = user && task.brand === user.id;
            
            return (
              <div
                key={task.id}
                className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition cursor-pointer"
                onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className="text-lg font-semibold text-white">{task.title}</h3>
                      <span className="bg-blue-500/20 text-blue-400 text-xs px-3 py-1 rounded">
                        {CATEGORY_LABELS[task.category]}
                      </span>
                      <span className="bg-purple-500/20 text-purple-400 text-xs px-3 py-1 rounded">
                        {getIncentiveDisplay(task)}
                      </span>
                      {hasApplied && (
                        <span className="bg-green-500/20 text-green-400 text-xs px-3 py-1 rounded">
                          Applied
                        </span>
                      )}
                      {isOwner && (
                        <span className="bg-yellow-500/20 text-yellow-400 text-xs px-3 py-1 rounded">
                          Your Task
                        </span>
                      )}
                    </div>
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">{task.description}</p>
                    <div className="flex items-center gap-6 text-sm text-gray-400">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDeadline(task.deadline)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        <span>{task.brand_username}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckSquare className="w-4 h-4" />
                        <span>{task.application_count} applicants</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          
          {filteredTasks.length === 0 && (
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-12 text-center">
              <CheckSquare className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No Tasks Found</h3>
              <p className="text-gray-400">No tasks match your current filter.</p>
            </div>
          )}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="bg-[#1a1a1a] rounded-lg border border-white/10 overflow-hidden">
          <table className="w-full">
            <thead className="bg-black/50 border-b border-white/10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Task</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Deadline</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Applicants</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {filteredTasks.map((task) => {
                const hasApplied = applications.some(app => app.task === task.id);
                const isOwner = user && task.brand === user.id;
                
                return (
                  <tr 
                    key={task.id}
                    onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                    className="hover:bg-white/5 cursor-pointer transition"
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-white">{task.title}</div>
                      <div className="text-sm text-gray-400 line-clamp-1">{task.description}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-300">{CATEGORY_LABELS[task.category]}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      {formatDeadline(task.deadline)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      {task.application_count}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {hasApplied && (
                          <span className="bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded">Applied</span>
                        )}
                        {isOwner && (
                          <span className="bg-yellow-500/20 text-yellow-400 text-xs px-2 py-1 rounded">Your Task</span>
                        )}
                        {!hasApplied && !isOwner && task.is_active && (
                          <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded">Open</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          
          {filteredTasks.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No tasks found</p>
            </div>
          )}
        </div>
      )}

      {/* Overview - Stats view */}
      {viewMode === 'overview' && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <div className="p-3 rounded-full bg-blue-500/20 w-fit mb-4">
                <CheckSquare className="w-6 h-6 text-blue-400" />
              </div>
              <p className="text-sm text-gray-400">Total Tasks</p>
              <p className="text-3xl font-bold text-white mt-1">{taskStats.total}</p>
            </div>

            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <div className="p-3 rounded-full bg-purple-500/20 w-fit mb-4">
                <Clock className="w-6 h-6 text-purple-400" />
              </div>
              <p className="text-sm text-gray-400">Active Tasks</p>
              <p className="text-3xl font-bold text-white mt-1">{taskStats.active}</p>
            </div>

            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <div className="p-3 rounded-full bg-green-500/20 w-fit mb-4">
                <User className="w-6 h-6 text-green-400" />
              </div>
              <p className="text-sm text-gray-400">My Tasks</p>
              <p className="text-3xl font-bold text-white mt-1">{taskStats.myTasks}</p>
            </div>

            <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6">
              <div className="p-3 rounded-full bg-yellow-500/20 w-fit mb-4">
                <AlertCircle className="w-6 h-6 text-yellow-400" />
              </div>
              <p className="text-sm text-gray-400">Applied</p>
              <p className="text-3xl font-bold text-white mt-1">{taskStats.applied}</p>
            </div>
          </div>

          <div className="bg-[#1a1a1a] rounded-lg border border-white/10 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Tasks</h3>
            <div className="space-y-3">
              {filteredTasks.slice(0, 5).map((task) => (
                <div
                  key={task.id}
                  onClick={() => router.push(`/dashboard/tasks/${task.id}`)}
                  className="flex items-center justify-between p-4 hover:bg-white/5 rounded-lg cursor-pointer transition"
                >
                  <div className="flex-1">
                    <h4 className="font-medium text-white">{task.title}</h4>
                    <p className="text-sm text-gray-400 line-clamp-1">{task.description}</p>
                  </div>
                  <div className="text-sm text-gray-400">
                    {formatDeadline(task.deadline)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
