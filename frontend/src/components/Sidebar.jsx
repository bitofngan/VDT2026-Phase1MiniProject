export default function Sidebar({ activePage, onPageChange }) {
  const items = [
    { id: "overview", label: "Overview" },
    { id: "weather", label: "Weather Map" },
    { id: "disasters", label: "Disaster Events" },
    { id: "forecast", label: "Risk Forecast" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">VN</div>
        <div>
          <div className="sidebar-title">Flood Risk</div>
          <div className="sidebar-subtitle">Control Center</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {items.map((item) => (
          <button
            key={item.id}
            className={
              activePage === item.id
                ? "sidebar-button active"
                : "sidebar-button"
            }
            onClick={() => onPageChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-title">System Version</div>
        <div>v1.0.0</div>
      </div>
    </aside>
  );
}