import { useEffect, useState } from "react";

export default function DisasterEventsPage() {
  const [activeEvents, setActiveEvents] = useState([]);
  const [historyEvents, setHistoryEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  async function loadEvents() {
    setIsLoading(true);

    try {
      const [activeRes, historyRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/disaster-events/active"),
        fetch("http://127.0.0.1:8000/api/disaster-events/history"),
      ]);

      const [activeData, historyData] = await Promise.all([
        activeRes.json(),
        historyRes.json(),
      ]);

      setActiveEvents(activeData);
      setHistoryEvents(historyData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load disaster events:", err);
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshDisasterInfo() {
    setIsRefreshing(true);

    try {
      await fetch("http://127.0.0.1:8000/api/disaster-events/refresh", {
        method: "POST",
      });

      await loadEvents();
    } catch (err) {
      console.error("Failed to refresh disaster events:", err);
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  return (
    <div className="disaster-page">
      <header className="disaster-header">
        <div>
          <h1>Disaster Events</h1>
          <p>
            Active storms, floods, and heavy rain events near Vietnam
            {lastUpdated ? ` · Updated ${lastUpdated.toLocaleTimeString()}` : ""}
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={refreshDisasterInfo}
          disabled={isRefreshing}
        >
          {isRefreshing ? "Refreshing..." : "Refresh disaster info"}
        </button>
      </header>

      <section className="disaster-summary-grid">
        <SummaryCard title="Active Events" value={activeEvents.length} />
        <SummaryCard
          title="Storms"
          value={activeEvents.filter((e) => e.type === "STORM").length}
        />
        <SummaryCard
          title="Floods"
          value={activeEvents.filter((e) => e.type === "FLOOD").length}
        />
        <SummaryCard
          title="Heavy Rain"
          value={activeEvents.filter((e) => e.type === "HEAVY_RAIN").length}
        />
      </section>

      <section className="disaster-card">
        <h2>Active Disaster Events</h2>

        {isLoading && <p className="muted-text">Loading disaster events...</p>}

        {!isLoading && activeEvents.length === 0 && (
          <p className="muted-text">
            No active storm, flood, or heavy rain events near Vietnam were found.
          </p>
        )}

        <div className="disaster-list">
          {activeEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </section>

      <section className="disaster-card">
        <h2>Recent Event Records</h2>

        <div className="table-wrapper">
          <table className="risk-table">
            <thead>
              <tr>
                <th>Fetched At</th>
                <th>Name</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Location</th>
                <th>Source</th>
              </tr>
            </thead>

            <tbody>
              {historyEvents.map((event) => (
                <tr key={event.id}>
                  <td>{event.fetched_at_utc || "-"}</td>
                  <td>{event.name || "-"}</td>
                  <td>{event.type || "-"}</td>
                  <td>{event.severity || "-"}</td>
                  <td>
                    {event.latitude && event.longitude
                      ? `${Number(event.latitude).toFixed(2)}, ${Number(
                          event.longitude
                        ).toFixed(2)}`
                      : "-"}
                  </td>
                  <td>{event.source || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!isLoading && historyEvents.length === 0 && (
            <div className="empty-table-message">
              No disaster history records yet.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function SummaryCard({ title, value }) {
  return (
    <div className="forecast-summary-card">
      <div>{title}</div>
      <strong>{value}</strong>
    </div>
  );
}

function EventCard({ event }) {
  return (
    <article className="event-card">
      <div className="event-card-top">
        <div>
          <h3>{event.name}</h3>
          <p>{event.description || "No description available."}</p>
        </div>

        <span className="event-badge">{event.type}</span>
      </div>

      <div className="event-meta">
        <span>Severity: {event.severity || "UNKNOWN"}</span>
        <span>Source: {event.source || "-"}</span>
        <span>Updated: {event.last_update_utc || "-"}</span>
      </div>

      {event.url && (
        <a href={event.url} target="_blank" rel="noreferrer">
          Open source
        </a>
      )}
    </article>
  );
}