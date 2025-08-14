export default function Header() {
  return (
    <header className="h-12 px-4 flex items-center justify-between border-b border-gray-700 bg-gray-900">
      <h1 className="text-lg font-semibold text-accent">FindersKeepers v2</h1>
      <div className="text-sm text-gray-400">Active Agent: <span className="text-accent">None</span></div>
    </header>
  );
}
