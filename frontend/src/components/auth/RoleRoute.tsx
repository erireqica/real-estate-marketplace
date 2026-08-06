import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type { Role } from '../../types'
export function RoleRoute({roles,children}:{roles:Role[];children:ReactNode}){const {user,loading}=useAuth();if(loading)return <div className="dashboard-empty">Restoring your session…</div>;if(!user)return <Navigate to="/" replace/>;if(!roles.includes(user.role))return <Navigate to="/" replace/>;return children}
