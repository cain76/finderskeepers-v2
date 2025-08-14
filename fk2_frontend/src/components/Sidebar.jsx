import { NavLink } from 'react-router-dom';
import { Home, Activity, Settings } from 'lucide-react';

const items = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/monitoring', label: 'Monitoring', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="bg-gray-800 w-56 text-gray-200 flex flex-col">
      <div className="p-4 text-2xl font-semibold text-accent">FK2</div>
      <nav className="flex-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center px-4 py-2 hover:bg-gray-700 ${isActive ? 'text-accent' : ''}`
            }
          >
            <Icon className="mr-2 h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
