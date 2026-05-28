import { VISUAL_LABEL } from "../labels";

export default function StatusPill({ state }) {
  return <span className={`pill pill-${state}`}>{VISUAL_LABEL[state]}</span>;
}
