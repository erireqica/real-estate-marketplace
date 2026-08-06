import { useState } from 'react'
import { X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export function AuthModal(){
  const auth=useAuth();const [mode,setMode]=useState<'login'|'register'>('login');const [error,setError]=useState('')
  if(!auth.showAuth)return null
  async function submit(form:FormData){setError('');try{const data=Object.fromEntries(form) as Record<string,string>;if(mode==='login')await auth.login(data.email,data.password);else await auth.register(data)}catch(error){setError(error instanceof Error?error.message:'Unable to continue.') }}
  return <div className="modal-backdrop" onMouseDown={auth.closeAuth}><section className="auth-modal" onMouseDown={event=>event.stopPropagation()}><button className="modal-close" onClick={auth.closeAuth} aria-label="Close"><X/></button><p className="eyebrow green">WELCOME TO HAVENLY</p><h2>{mode==='login'?'Welcome back':'Create your account'}</h2><p>{mode==='login'?'Sign in to save homes and contact agents.':'Join to save properties, send inquiries and apply as an agent.'}</p><form action={submit}>{mode==='register'&&<div className="form-row"><input name="firstName" placeholder="First name" required/><input name="lastName" placeholder="Last name" required/></div>}<input type="email" name="email" placeholder="Email address" required/><input type="password" name="password" placeholder="Password (8+ characters)" minLength={8} required/>{error&&<div className="form-error">{error}</div>}<button className="primary-button">{mode==='login'?'Sign in':'Create account'}</button></form><button className="text-button" onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login'?'New here? Create an account':'Already registered? Sign in'}</button></section></div>
}
