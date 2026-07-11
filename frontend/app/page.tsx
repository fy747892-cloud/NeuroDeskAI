import { getHealthStatus } from "@/lib/api";
import { AuthPanel } from "@/components/auth-panel";

const navItems = ["Dashboard", "Tasks", "Appointments", "AI Chat", "Contacts", "Files"];

const metrics = [
  { label: "Open tasks", value: "24", trend: "+6 today" },
  { label: "Pending AI approvals", value: "8", trend: "3 high confidence" },
  { label: "Upcoming appointments", value: "12", trend: "Next at 14:30" },
  { label: "Documents indexed", value: "146", trend: "18 new" },
];

const workQueue = [
  {
    title: "Approve AI follow-up task",
    detail: "Conversation analysis suggested a patient onboarding checklist.",
    status: "AI approval",
    time: "09:20",
  },
  {
    title: "Review appointment conflict",
    detail: "Two callbacks overlap for the same organization contact.",
    status: "Calendar",
    time: "10:05",
  },
  {
    title: "Sync email account",
    detail: "Gmail provider is ready for the next message ingestion run.",
    status: "Email",
    time: "11:10",
  },
  {
    title: "Reindex uploaded document",
    detail: "A PDF extraction completed and can be added to semantic search.",
    status: "Files",
    time: "12:40",
  },
];

const aiSignals = [
  { name: "Conversation analysis", state: "Mock by default", value: "Ready" },
  { name: "OpenAI-compatible LLM", state: "Env controlled", value: "Optional" },
  { name: "Tenant-scoped retrieval", state: "Context gated", value: "Active" },
];

export default async function Home() {
  const health = await getHealthStatus();

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <div className="brandMark">N</div>
          <div>
            <strong>NeuroDeskAI</strong>
            <span>Operations</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <a href="#" className={item === "Dashboard" ? "active" : ""} key={item}>
              {item}
            </a>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Workspace overview</p>
            <h1>Dashboard</h1>
          </div>
          <div className={`status ${health.ok ? "online" : "offline"}`}>
            <span aria-hidden="true" />
            {health.label}
          </div>
        </header>

        <section className="metrics" aria-label="Key metrics">
          {metrics.map((metric) => (
            <article className="metric" key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.trend}</small>
            </article>
          ))}
        </section>

        <section className="contentGrid">
          <div className="panel queuePanel">
            <div className="panelHeader">
              <h2>Priority Queue</h2>
              <button type="button">Refresh</button>
            </div>
            <div className="queueList">
              {workQueue.map((item) => (
                <article className="queueItem" key={item.title}>
                  <time>{item.time}</time>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.detail}</p>
                  </div>
                  <span>{item.status}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="panel aiPanel">
            <div className="panelHeader">
              <h2>AI Layer</h2>
              <span className="tag">LLM ready</span>
            </div>
            <div className="signalList">
              {aiSignals.map((signal) => (
                <div className="signal" key={signal.name}>
                  <div>
                    <strong>{signal.name}</strong>
                    <span>{signal.state}</span>
                  </div>
                  <b>{signal.value}</b>
                </div>
              ))}
            </div>
          </div>

          <div className="panel accessPanel">
            <AuthPanel />
          </div>
        </section>
      </section>
    </main>
  );
}
