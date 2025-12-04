"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useUser } from "@/hooks/use-user";
import { getCurrentUser } from "@/lib/auth";
import { userApi, type UserProfile } from "@/lib/user-api";
import { UserAvatar } from "@/components/user-avatar";
import {
  Home,
  Building2,
  Twitter,
  Instagram,
  BarChart3,
  Settings,
  Users,
  Menu,
  X,
  ChevronDown,
  Search,
  Grid3x3,
  MessageSquare,
  CheckSquare,
  Briefcase,
  TrendingUp,
  Calendar,
  Contact,
  DollarSign,
  FileText,
  UserCircle,
  Workflow,
  Loader2,
} from "lucide-react";
import { Toaster } from "sonner";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarHovered, setSidebarHovered] = useState(false);
  const [orgDropdownOpen, setOrgDropdownOpen] = useState(false);
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);
  const [brands, setBrands] = useState<any[]>([]);
  const [brandsLoading, setBrandsLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();
  const user = useUser();
  const [authChecked, setAuthChecked] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // Auth protection - allow certain routes without authentication
  useEffect(() => {
    async function checkAuth() {
      // Allow /feed page without auth
      if (pathname === '/feed') {
        setAuthChecked(true);
        return;
      }

      // Allow public workspace viewing by slug (pattern: /flow-generator/[slug])
      // Slugs are 12 characters (UUID prefix)
      if (/^\/flow-generator\/[a-f0-9-]{8,}/.test(pathname)) {
        setAuthChecked(true);
        return;
      }

      // Allow public user profiles (/users/[id])
      if (/^\/users\/\d+/.test(pathname)) {
        setAuthChecked(true);
        return;
      }

      // All other dashboard routes require authentication
      const currentUser = await getCurrentUser();
      if (!currentUser) {
        router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
        return;
      }
      
      setAuthChecked(true);
    }

    checkAuth();
  }, [pathname, router]);

  // Load user profile with picture
  useEffect(() => {
    async function loadProfile() {
      if (user) {
        try {
          const profile = await userApi.getCurrentProfile();
          setUserProfile(profile);
        } catch (err) {
          console.error('Failed to load profile:', err);
        }
      }
    }
    loadProfile();
  }, [user]);

  // Load brands for Twitter navigation visibility
  useEffect(() => {
    async function loadBrands() {
      if (user && authChecked) {
        try {
          const response = await fetch('/api/brands/');
          if (response.ok) {
            const brandsData = await response.json();
            setBrands(brandsData);
          } else {
            // Fallback to mock data if Django server is not running
            console.warn('Django API not available, using mock brands data');
            setBrands([
              { id: 1, name: 'gemnarr', slug: 'gemnarr', has_twitter_config: false },
              { id: 2, name: 'nn', slug: 'nn', has_twitter_config: false }
            ]);
          }
        } catch (err) {
          console.error('Failed to load brands:', err);
          // Fallback to mock data on network error
          setBrands([
            { id: 1, name: 'gemnarr', slug: 'gemnarr', has_twitter_config: false },
            { id: 2, name: 'nn', slug: 'nn', has_twitter_config: false }
          ]);
        } finally {
          setBrandsLoading(false);
        }
      }
    }
    loadBrands();
  }, [user, authChecked]);

  // Show loading state while checking auth
  if (!authChecked) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Get user data from actual auth system
  const userData = {
    username: user?.name || user?.email?.split('@')[0] || "User",
    plan: "Pro Plan", // TODO: Get actual plan from user data
    avatar: (user?.name || user?.email || "U").substring(0, 2).toUpperCase()
  };

  const navigation = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Feed", href: "/feed", icon: Grid3x3 },
    { name: "Flow Generator", href: "/flow-generator", icon: Workflow },
    { name: "Brands", href: "/dashboard/brands", icon: Building2 },
  ];

  // Check if any brand has Twitter configured
  const hasTwitterConfigured = brands.some(brand => brand.has_twitter_config);

  const twitter = hasTwitterConfigured ? [
    { name: "Tweet Queue", href: "/dashboard/twitter/queue", icon: Calendar },
    { name: "Analytics", href: "/dashboard/twitter/analytics", icon: TrendingUp },
    { name: "Configuration", href: "/dashboard/twitter/config", icon: Settings },
    { name: "History", href: "/dashboard/twitter/history", icon: FileText },
  ] : [
    { name: "Setup Required", href: "/dashboard/twitter/config", icon: Settings },
  ];

  const instagram = [
    { name: "Post Queue", href: "/dashboard/instagram/queue", icon: Calendar },
    { name: "Connect", href: "/dashboard/instagram/connect", icon: Instagram },
  ];

  const crm = [
    { name: "Dashboard", href: "/dashboard/crm", icon: BarChart3 },
    { name: "Companies", href: "/dashboard/crm/companies", icon: Building2 },
    { name: "Contacts", href: "/dashboard/crm/contacts", icon: Contact },
    { name: "Deals", href: "/dashboard/crm/deals", icon: DollarSign },
    { name: "Tasks", href: "/dashboard/crm/tasks", icon: CheckSquare },
    { name: "Reports", href: "/dashboard/crm/reports", icon: FileText },
  ];

  const analytics = [
    { name: "Dashboard", href: "/dashboard/analytics", icon: BarChart3 },
    { name: "Pages", href: "/dashboard/analytics/pages", icon: FileText },
    { name: "Events", href: "/dashboard/analytics/events", icon: TrendingUp },
    { name: "Sessions", href: "/dashboard/analytics/sessions", icon: Users },
  ];

  const tasks = [
    { name: "Active Tasks", href: "/dashboard/tasks", icon: CheckSquare },
    { name: "All Tasks", href: "/dashboard/tasks/all", icon: FileText },
    { name: "Create Task", href: "/dashboard/tasks/create", icon: Calendar },
  ];

  const chat = [
    { name: "Messages", href: "/dashboard/chat", icon: MessageSquare },
    { name: "Conversations", href: "/dashboard/chat/conversations", icon: Users },
  ];

  const settings = [
    { name: "Profile", href: "/dashboard/profile", icon: UserCircle },
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <div className="min-h-screen bg-black text-white flex relative">
      <Toaster position="bottom-right" />
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Floating Sidebar */}
      <aside
        onMouseEnter={() => setSidebarHovered(true)}
        onMouseLeave={() => setSidebarHovered(false)}
        className={`
          fixed top-4 bottom-4 left-4 z-50
          transform transition-all duration-300 ease-in-out
          rounded-3xl overflow-hidden
          shadow-[ -18px_0_30px_rgba(255,255,255,0.37),
                   18px_0_30px_rgba(255,255,255,0.37),
                   0_0_45px_rgba(0,0,0,0.25) ]
          ${sidebarOpen ? "translate-x-0 w-64" : "-translate-x-full lg:translate-x-0"}
          ${!sidebarOpen && "lg:w-16 lg:hover:w-64"}
        `}
      >
        {/* TRUE CANVA STYLE GLASS BACKGROUND */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#131317]/95 via-[#101014]/90 to-[#060608]/95 backdrop-blur-2xl" />

        {/* Subtle inner border */}
        <div className="absolute inset-0 ring-1 ring-white/10 rounded-3xl" />

        {/* Soft inner glow */}
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.06),transparent_70%)]" />

        <div className="relative flex flex-col h-full p-4">
          {/* User Profile & Plan */}
          <Link
            href="/dashboard/profile"
            className={`flex items-center transition-all group rounded-xl hover:bg-white/5 ${sidebarHovered ? 'justify-between p-3' : 'justify-center p-2'}`}
          >
            {sidebarHovered ? (
              <>
                <div className="flex items-center gap-3 min-w-0">
                  <UserAvatar 
                    user={userProfile} 
                    size="md"
                    className="flex-shrink-0"
                  />
                  <div className="text-left leading-tight transition-all duration-300 opacity-100 w-auto">
                    <div className="text-sm font-medium whitespace-nowrap">{userData.username}</div>
                    <div className="text-xs text-gray-400 whitespace-nowrap">{userData.plan}</div>
                  </div>
                </div>
                <UserCircle className="w-4 h-4 text-gray-400 group-hover:text-gray-300 transition-all duration-300 flex-shrink-0 opacity-100" />
              </>
            ) : (
              <UserAvatar 
                user={userProfile} 
                size="md"
                className="flex-shrink-0"
              />
            )}
          </Link>

          {/* Search */}
          <div className={`relative mt-5 transition-all duration-300 ${sidebarHovered ? 'opacity-100' : 'lg:opacity-0 lg:h-0 lg:mt-0 lg:overflow-hidden'}`}>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search"
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Scroll Area */}
          <nav className="flex-1 mt-6 overflow-y-auto space-y-7 scrollbar-hide hover:scrollbar-show">
            {/* Main Menu - No Dropdown */}
            <Section label="MAIN MENU" items={navigation} isActive={isActive} sidebarHovered={sidebarHovered} />

            {/* Socials - Hover Dropdown */}
            <DropdownSection 
              label="SOCIALS" 
              icon={Twitter}
              subSections={[
                { 
                  label: hasTwitterConfigured ? "Twitter" : "Twitter (Setup Required)", 
                  items: twitter,
                  needsSetup: !hasTwitterConfigured
                },
                { label: "Instagram", items: instagram }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />

            {/* CRM - Hover Dropdown */}
            <DropdownSection 
              label="CRM" 
              icon={Building2}
              subSections={[
                { label: "CRM", items: crm }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />

            {/* Analytics - Hover Dropdown */}
            <DropdownSection 
              label="ANALYTICS" 
              icon={BarChart3}
              subSections={[
                { label: "Analytics", items: analytics }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />

            {/* Tasks - Hover Dropdown */}
            <DropdownSection 
              label="TASKS" 
              icon={CheckSquare}
              subSections={[
                { label: "Tasks", items: tasks }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />

            {/* Chat - Hover Dropdown */}
            <DropdownSection 
              label="CHAT" 
              icon={MessageSquare}
              subSections={[
                { label: "Chat", items: chat }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />

            {/* Settings - Hover Dropdown */}
            <DropdownSection 
              label="SETTINGS" 
              icon={Settings}
              subSections={[
                { label: "Settings", items: settings }
              ]}
              isActive={isActive}
              hoveredSection={hoveredSection}
              setHoveredSection={setHoveredSection}
              sidebarHovered={sidebarHovered}
            />
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 p-8 mt-4 transition-all duration-300 ${sidebarHovered ? 'lg:ml-72' : 'lg:ml-20'}`}>{children}</main>

      {/* Mobile Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white/10 backdrop-blur-xl rounded-xl"
      >
        {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>
    </div>
  );
}

function Section({
  label,
  items,
  isActive,
  sidebarHovered,
}: {
  label: string;
  items: any[];
  isActive: (href: string) => boolean;
  sidebarHovered: boolean;
}) {
  return (
    <div>
      <h3 className={`text-[10px] font-semibold text-gray-500 uppercase mb-2 tracking-wider transition-all duration-300 ${sidebarHovered ? 'opacity-100' : 'lg:opacity-0 lg:h-0 lg:mb-0 lg:overflow-hidden'}`}>
        {label}
      </h3>
      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              title={!sidebarHovered ? item.name : undefined}
              className={`
                flex items-center transition-all relative group/item
                ${sidebarHovered ? 'gap-3 px-3 py-2' : 'justify-center p-2'} 
                rounded-lg text-sm
                ${
                  isActive(item.href)
                    ? "bg-white/10 text-white"
                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                }
              `}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className={`transition-all duration-300 whitespace-nowrap ${sidebarHovered ? 'opacity-100 w-auto' : 'lg:opacity-0 lg:w-0 lg:overflow-hidden'}`}>
                {item.name}
              </span>
              
              {/* Tooltip for collapsed state */}
              {!sidebarHovered && (
                <div className="hidden lg:block absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover/item:opacity-100 pointer-events-none transition-opacity z-50">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function DropdownSection({
  label,
  icon,
  subSections,
  isActive,
  hoveredSection,
  setHoveredSection,
  sidebarHovered,
}: {
  label: string;
  icon: any;
  subSections: { label: string; items: any[]; needsSetup?: boolean }[];
  isActive: (href: string) => boolean;
  hoveredSection: string | null;
  setHoveredSection: (section: string | null) => void;
  sidebarHovered: boolean;
}) {
  const Icon = icon;
  const isOpen = hoveredSection === label && sidebarHovered;

  return (
    <div
      className="relative"
      onMouseEnter={() => sidebarHovered && setHoveredSection(label)}
      onMouseLeave={() => setHoveredSection(null)}
    >
      {/* Expanded view */}
      {sidebarHovered ? (
        <>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
              {label}
            </h3>
            <Icon className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
          </div>

          {/* Dropdown Content */}
          <div
            className={`
              overflow-hidden transition-all duration-300 ease-in-out
              ${isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}
            `}
          >
            <div className="space-y-4 pl-2 border-l border-white/10">
              {subSections.map((subSection) => (
                <div key={subSection.label}>
                  {subSections.length > 1 && (
                    <div className="flex items-center gap-2 mb-1 pl-2">
                      <h4 className="text-[9px] font-semibold text-gray-600 uppercase tracking-wider">
                        {subSection.label}
                      </h4>
                      {subSection.needsSetup && (
                        <span className="text-[8px] px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded-full">
                          SETUP
                        </span>
                      )}
                    </div>
                  )}
                  <div className="space-y-1">
                    {subSection.items.map((item) => {
                      const ItemIcon = item.icon;
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className={`
                            flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                            transition-all
                            ${
                              isActive(item.href)
                                ? "bg-white/10 text-white"
                                : "text-gray-400 hover:bg-white/5 hover:text-white"
                            }
                          `}
                        >
                          <ItemIcon className="w-5 h-5 flex-shrink-0" />
                          <span className="whitespace-nowrap">{item.name}</span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        /* Collapsed icon-only display */
        <div className="flex justify-center">
          <div className="relative group/section">
            <div className="p-2 rounded-lg hover:bg-white/5 cursor-pointer flex items-center justify-center">
              <Icon className="w-5 h-5 text-gray-400" />
            </div>
            {/* Tooltip */}
            <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover/section:opacity-100 pointer-events-none transition-opacity z-50 top-1/2 -translate-y-1/2">
              {label}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
