import { Link } from 'react-router-dom'
export function PlaceholderPage({title}:{title:string}){return <section className="placeholder"><p className="eyebrow green">HAVENLY</p><h1>{title}</h1><p>The page you requested could not be found.</p><Link className="primary-link" to="/">Return home</Link></section>}
