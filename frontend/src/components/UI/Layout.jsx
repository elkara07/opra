import { NavLink, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store';
import { useState } from 'react';
import {
  HomeIcon,
  TicketIcon,
  UserGroupIcon,
  FolderIcon,
  MapIcon,
  ClockIcon,
  ArrowUpIcon,
  EnvelopeIcon,
  PhoneIcon,
  LinkIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ServerIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

const NAV_SECTIONS = [
  {
    title: 'Operations',
    items: [
      { to: '/', label: 'Dashboard', icon: HomeIcon, end: true },
      { to: '/tickets', label: 'Tickets', icon: TicketIcon },
      { to: '/contacts', label: 'Contacts', icon: UserGroupIcon },
      { to: '/projects', label: 'Projects', icon: FolderIcon },
    ],
  },
  {
    title: 'Topology',
    items: [
      { to: '/topology', label: 'Pipeline Map', icon: MapIcon },
      { to: '/voice-test', label: 'Voice Test', icon: PhoneIcon },
    ],
  },
  {
    title: 'Settings',
    managerOnly: true,
    items: [
      { to: '/settings/sla', label: 'SLA', icon: ClockIcon },
      { to: '/settings/escalation', label: 'Escalation', icon: ArrowUpIcon },
      { to: '/settings/email', label: 'Email', icon: EnvelopeIcon },
      { to: '/settings/voice', label: 'Voice', icon: PhoneIcon },
      { to: '/settings/jira', label: 'Jira', icon: LinkIcon },
      { to: '/settings/ldap', label: 'LDAP', icon: ShieldCheckIcon },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { to: '/reports', label: 'Reports', icon: ChartBarIcon },
      { to: '/system', label: 'System Health', icon: ServerIcon },
    ],
  },
];

const ROLE_BADGE_COLORS = {
  admin: 'bg-red-100 text-red-700',
  manager: 'bg-blue-100 text-blue-700',
  agent: 'bg-green-100 text-green-700',
  viewer: 'bg-gray-100 text-gray-600',
};

export default function Layout({ children }) {
  const { user, logout } = useAuthStore();
  const role = user?.role || 'agent';
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState({});
  const location = useLocation();

  const isManagerPlus = ['manager', 'tenant_admin', 'super_admin', 'admin', 'agent_l3'].includes(role);

  function toggleSection(title) {
    setCollapsedSections((prev) => ({ ...prev, [title]: !prev[title] }));
  }

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-600 text-white'
        : 'text-slate-300 hover:bg-slate-700 hover:text-white'
    }`;

  const sidebar = (
    <aside className="flex flex-col w-60 bg-slate-800 text-white h-full">
      {/* Brand */}
      <div className="px-5 py-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
            CC
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">CallCenter</h1>
            <p className="text-[10px] text-slate-400">Ticket Management</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-4">
        {NAV_SECTIONS.map((section) => {
          if (section.managerOnly && !isManagerPlus) return null;
          const isCollapsed = collapsedSections[section.title];
          return (
            <div key={section.title}>
              <button
                onClick={() => toggleSection(section.title)}
                className="flex items-center justify-between w-full px-2 mb-1"
              >
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  {section.title}
                </span>
                <ChevronDownIcon
                  className={`w-3 h-3 text-slate-500 transition-transform ${
                    isCollapsed ? '-rotate-90' : ''
                  }`}
                />
              </button>
              {!isCollapsed && (
                <div className="space-y-0.5">
                  {section.items.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={navLinkClass}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <item.icon className="w-5 h-5 flex-shrink-0" />
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="px-4 py-3 border-t border-slate-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-bold text-white">
            {(user?.full_name || user?.email || 'U')[0].toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-white truncate">
              {user?.full_name || user?.email || 'User'}
            </p>
            <span
              className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                ROLE_BADGE_COLORS[role] || ROLE_BADGE_COLORS.agent
              }`}
            >
              {role.toUpperCase()}
            </span>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-700 hover:text-red-400 transition-colors"
        >
          <ArrowRightOnRectangleIcon className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Mobile toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-white shadow-md border border-gray-200 text-gray-600"
      >
        {sidebarOpen ? (
          <XMarkIcon className="w-5 h-5" />
        ) : (
          <Bars3Icon className="w-5 h-5" />
        )}
      </button>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex flex-shrink-0">{sidebar}</div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <>
          <div
            className="lg:hidden fixed inset-0 bg-black/40 z-40"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="lg:hidden fixed inset-y-0 left-0 z-50 w-60">{sidebar}</div>
        </>
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
