import { useEffect, useState } from 'react';

const servicesOrder = [
  'fastapi',
  'postgres',
  'qdrant',
  'neo4j',
  'redis',
  'ollama'
];

export default function Dashboard() {
  const [services, setServices] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/health');
        const data = await res.json();
        setServices(data.services || {});
      } catch (err) {
        console.error('Failed to load system health', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-accent">Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {servicesOrder.map(key => {
          const svc = services[key] || {};
          const status = svc.status || 'unknown';
          const color = status === 'up' ? 'text-green-400' : status === 'down' ? 'text-red-400' : 'text-yellow-400';
          const label = key.charAt(0).toUpperCase() + key.slice(1);
          return (
            <div key={key} className="p-4 rounded bg-gray-800">
              <p className="text-sm text-gray-400">{label}</p>
              <p className={`font-semibold ${color}`}>{status}</p>
            </div>
          );
        })}
      </div>
      {loading && <p className="text-gray-500">Loading...</p>}
    </div>
  );
}
