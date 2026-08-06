import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import type { User } from '../types'
import { api } from '../services/api'

type AuthContextValue={user:User|null;loading:boolean;showAuth:boolean;savedIds:Set<number>;unread:number;openAuth:()=>void;closeAuth:()=>void;login:(email:string,password:string)=>Promise<void>;register:(data:Record<string,string>)=>Promise<void>;logout:()=>void;refreshFavorites:()=>Promise<void>;toggleFavorite:(id:number)=>Promise<boolean>;refreshUnread:()=>Promise<void>}
const AuthContext=createContext<AuthContextValue|null>(null)

export function AuthProvider({children}:{children:ReactNode}){const navigate=useNavigate();const [user,setUser]=useState<User|null>(null);const [loading,setLoading]=useState(Boolean(localStorage.getItem('accessToken')));const [showAuth,setShowAuth]=useState(false);const [savedIds,setSavedIds]=useState(new Set<number>());const [unread,setUnread]=useState(0);const session=useRef(0)
  function clearAccount(){session.current+=1;setUser(null);setSavedIds(new Set());setUnread(0);setShowAuth(false)}
  async function refreshFavorites(){const active=session.current;const r=await api.favoriteIds();if(active===session.current)setSavedIds(new Set(r.ids))}
  async function refreshUnread(){const active=session.current;const r=await api.unreadCount();if(active===session.current)setUnread(r.count)}
  useEffect(()=>{const active=session.current;if(localStorage.getItem('accessToken'))api.me().then(r=>{if(active!==session.current)return;setUser(r.user);void refreshFavorites();void refreshUnread()}).catch(()=>{localStorage.removeItem('accessToken');localStorage.removeItem('refreshToken');clearAccount()}).finally(()=>setLoading(false));else setLoading(false)},[])
  function accept(result:{user:User;accessToken:string;refreshToken:string}){clearAccount();localStorage.setItem('accessToken',result.accessToken);localStorage.setItem('refreshToken',result.refreshToken);setUser(result.user);setLoading(false);setShowAuth(false);void refreshFavorites();void refreshUnread();navigate('/',{replace:true})}
  async function toggleFavorite(id:number){const next=!savedIds.has(id);if(next)await api.saveFavorite(id);else await api.removeFavorite(id);setSavedIds(current=>{const copy=new Set(current);if(next)copy.add(id);else copy.delete(id);return copy});return next}
  function logout(){localStorage.removeItem('accessToken');localStorage.removeItem('refreshToken');clearAccount();navigate('/',{replace:true})}
  return <AuthContext.Provider value={{user,loading,showAuth,savedIds,unread,openAuth:()=>setShowAuth(true),closeAuth:()=>setShowAuth(false),login:async(email,password)=>accept(await api.login(email,password)),register:async data=>accept(await api.register(data)),logout,refreshFavorites,toggleFavorite,refreshUnread}}>{children}</AuthContext.Provider>}
export function useAuth(){const context=useContext(AuthContext);if(!context)throw new Error('AuthProvider is missing');return context}
