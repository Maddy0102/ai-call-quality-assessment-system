import { Settings as SettingsIcon } from "lucide-react";

function Settings() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="text-slate-400 text-sm mt-2">
        Manage application configuration.
      </p>

      <div className="mt-8 bg-[#111827] border border-slate-800 rounded-2xl p-8">
        <SettingsIcon size={30} className="text-violet-400 mb-4" />
        <h2 className="font-semibold">Application Settings</h2>
        <p className="text-sm text-slate-500 mt-2">
          Checklist configuration, AI preferences and system settings
          will be available here.
        </p>
      </div>
    </div>
  );
}

export default Settings;
