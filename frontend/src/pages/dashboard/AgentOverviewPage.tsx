import { Building2, Eye, Mail, MailOpen } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AgentOverview } from '../../services/api'
import { StatCards } from '../../components/dashboard/StatCards'
export function AgentOverviewPage(){const [data,setData]=useState<AgentOverview>();useEffect(()=>{api.agentOverview().then(setData)},[]);if(!data)return <div className="dashboard-empty">Loading overview…</div>;return <><div className="dashboard-title"><div><p>AGENT OVERVIEW</p><h1>Welcome back</h1></div><Link className="primary-button" to="/agent/properties">Manage properties</Link></div><StatCards items={[[Building2,data.activeListings,'Active listings'],[Eye,data.totalViews,'Total property views'],[Mail,data.inquiries,'Total inquiries'],[MailOpen,data.unreadInquiries,'Unread messages']]}/><section className="dashboard-panel"><div className="panel-heading"><h2>Recently added</h2><Link to="/agent/properties">View all</Link></div>{data.recentProperties.length?<div className="compact-list">{data.recentProperties.map(item=><div key={item.id}><img src={item.imageUrl}/><span><strong>{item.title}</strong><small>{item.city} · {item.views} views</small></span><b>€{item.price.toLocaleString()}</b></div>)}</div>:<div className="dashboard-empty">Your newest listings will appear here.</div>}</section></>}

