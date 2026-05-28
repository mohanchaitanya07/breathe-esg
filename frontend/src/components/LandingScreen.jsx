import { ANALYST } from "../api";

export default function LandingScreen({ onEnter }) {
  return (
    <div className="landing">
      <div className="landing-card">
        <div className="landing-mark">◐</div>
        <h1 className="landing-title">Breathe ESG</h1>
        <p className="landing-tagline">
          Ingest, normalize, and review carbon emissions data for audit.
        </p>
        <button className="btn btn-primary landing-btn" onClick={onEnter}>
          Enter Dashboard
        </button>
        <p className="landing-demo">Demo — signed in as {ANALYST}</p>
      </div>
    </div>
  );
}
