import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  Headphones,
  Settings,
  AudioLines,
  Activity,
  Bell,
  Search,
  ChevronDown
} from "lucide-react";

const navigation = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Upload Audio", path: "/upload", icon: Upload },
  { name: "Call History", path: "/calls", icon: Headphones },
  { name: "Settings", path: "/settings", icon: Settings }
];

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-[#0b1020] text-slate-100 flex">

      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] border-r border-slate-800 flex flex-col fixed inset-y-0 left-0 z-20">

        <div className="h-20 flex items-center gap-3 px-6 border-b border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-violet-600 flex items-center justify-center">
            <AudioLines size={23} />
          </div>

          <div>
            <h1 className="font-bold text-lg tracking-tight">CallIQ</h1>
            <p className="text-xs text-slate-500">AI Quality Intelligence</p>
          </div>
        </div>

        <div className="px-4 py-7">
          <p className="text-xs uppercase tracking-widest text-slate-500 px-3 mb-4">
            Workspace
          </p>

          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition ${
                      isActive
                        ? "bg-violet-600/20 text-violet-300 border border-violet-500/20"
                        : "text-slate-400 hover:bg-slate-800 hover:text-white"
                    }`
                  }
                >
                  <Icon size={19} />
                  {item.name}
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto p-4">
          <div className="bg-slate-800/70 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={16} className="text-emerald-400" />
              <span className="text-sm font-medium">System Status</span>
            </div>
            <p className="text-xs text-slate-400">
              AI Call Quality System
            </p>
            <div className="flex items-center gap-2 mt-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs text-emerald-400">Development mode</span>
            </div>
          </div>

          <p className="text-xs text-slate-600 text-center mt-5">
            CallIQ v1.0.0
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 ml-64 min-w-0">

        <header className="h-20 border-b border-slate-800 bg-[#0e1525] flex items-center justify-between px-8 sticky top-0 z-10">

          <div className="relative w-80">
            <Search
              size={17}
              className="absolute left-3 top-3 text-slate-500"
            />
            <input
              type="text"
              placeholder="Search..."
              className="w-full bg-slate-800/60 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-sm outline-none focus:border-violet-500"
            />
          </div>

          <div className="flex items-center gap-5">
            <button className="text-slate-400 hover:text-white">
              <Bell size={20} />
            </button>

            <div className="flex items-center gap-3 border-l border-slate-700 pl-5">
              <div className="w-9 h-9 rounded-full bg-violet-600 flex items-center justify-center font-bold">
                M
              </div>
              <div>
                <p className="text-sm font-medium">Administrator</p>
                <p className="text-xs text-slate-500">Admin</p>
              </div>
              <ChevronDown size={16} className="text-slate-500" />
            </div>
          </div>
        </header>

        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
