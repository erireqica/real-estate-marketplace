import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { User } from '../types'
import { api } from '../services/api'

type AuthContextValue={user:User|null;loading:boolean;showAuth:boolean;openAuth:()=>void;closeAuth:()=>void;login:(email:string,password:string)=>Promise<void>;register:(data:Record<string,string>)=>Promise<void>;logout:()=>void}
const AuthContext=createContext<AuthContextValue|null>(null)

export function AuthProvider({children}:{children:ReactNode}){
  const [user,setUser]=useState<User|null>(null)
  const [loading,setLoading]=useState(Boolean(localStorage.getItem('accessToken')))
  const [showAuth,setShowAuth]=useState(false)
  useEffect(()=>{if(localStorage.getItem('accessToken'))api.me().then(r=>setUser(r.user)).catch(()=>localStorage.removeItem('accessToken')).finally(()=>setLoading(false))},[])
  function accept(result:{user:User;accessToken:string;refreshToken:string}){localStorage.setItem('accessToken',result.accessToken);localStorage.setItem('refreshToken',result.refreshToken);setUser(result.user);setShowAuth(false)}
  return <AuthContext.Provider value={{user,loading,showAuth,openAuth:()=>setShowAuth(true),closeAuth:()=>setShowAuth(false),login:async(email,password)=>accept(await api.login(email,password)),register:async data=>accept(await api.register(data)),logout:()=>{localStorage.clear();setUser(null)}}}>{children}</AuthContext.Provider>
}
export function useAuth(){const context=useContext(AuthContext);if(!context)throw new Error('AuthProvider is missing');return context}
