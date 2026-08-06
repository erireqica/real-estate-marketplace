import type { LucideIcon } from 'lucide-react'
export function StatCards({items}:{items:[LucideIcon,string|number,string][]}){return <div className="dashboard-stats">{items.map(([Icon,value,label])=><article key={label}><Icon/><div><strong>{value}</strong><span>{label}</span></div></article>)}</div>}
