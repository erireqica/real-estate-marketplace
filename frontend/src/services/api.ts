import type { Paginated, Property, User } from '../types'
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000/api'

export class ApiError extends Error { constructor(message:string, public status:number){ super(message) } }
async function request<T>(path:string, options?:RequestInit,retry=true):Promise<T>{
  const token=localStorage.getItem('accessToken')
  const isForm=options?.body instanceof FormData
  const response=await fetch(`${API_URL}${path}`,{...options,headers:{...(!isForm?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`} :{}),...options?.headers}})
  if(response.status===401&&retry&&localStorage.getItem('refreshToken')){
    const refreshed=await fetch(`${API_URL}/auth/refresh`,{method:'POST',headers:{Authorization:`Bearer ${localStorage.getItem('refreshToken')}`}})
    if(refreshed.ok){const data=await refreshed.json();localStorage.setItem('accessToken',data.accessToken);return request<T>(path,options,false)}
    localStorage.removeItem('accessToken');localStorage.removeItem('refreshToken')
  }
  const body=await response.json().catch(()=>({}))
  if(!response.ok) throw new ApiError(body.error?.message ?? 'Something went wrong.',response.status)
  return body as T
}
export const api={
  properties:(params=new URLSearchParams())=>request<Paginated<Property>>(`/properties?${params}`),
  property:(slug:string)=>request<{property:Property}>(`/properties/${slug}`),
  login:(email:string,password:string)=>request<AuthResult>('/auth/login',{method:'POST',body:JSON.stringify({email,password})}),
  register:(data:Record<string,string>)=>request<AuthResult>('/auth/register',{method:'POST',body:JSON.stringify(data)}),
  me:()=>request<{user:User}>('/auth/me'),
  market:(city='')=>request<MarketStats>(`/market/overview${city?`?city=${encodeURIComponent(city)}`:''}`),
  trends:(city='')=>request<TrendResult>(`/market/trends${city?`?city=${encodeURIComponent(city)}`:''}`),
  inquiry:(propertyId:number,message:string)=>request<{message:string}>('/account/inquiries',{method:'POST',body:JSON.stringify({propertyId,message})}),
  applyAgent:(data:FormData)=>request<{id:number;status:string}>('/account/agent-application',{method:'POST',body:data}),
  favorites:()=>request<{items:Property[]}>('/account/favorites'),
  saveFavorite:(id:number)=>request<{saved:boolean}>(`/account/favorites/${id}`,{method:'PUT'}),
  removeFavorite:(id:number)=>request<void>(`/account/favorites/${id}`,{method:'DELETE'}),
  favoriteIds:()=>request<{ids:number[]}>('/account/favorite-ids'),
  updateProfile:(data:Record<string,string>)=>request<{user:User}>('/account/profile',{method:'PATCH',body:JSON.stringify(data)}),
  changePassword:(currentPassword:string,newPassword:string)=>request<{message:string}>('/account/change-password',{method:'POST',body:JSON.stringify({currentPassword,newPassword})}),
  conversations:()=>request<{items:Conversation[]}>('/account/conversations'),
  conversation:(id:number)=>request<{conversation:Conversation}>(`/account/conversations/${id}`),
  reply:(id:number,message:string)=>request<{message:string}>(`/account/conversations/${id}/messages`,{method:'POST',body:JSON.stringify({message})}),
  unreadCount:()=>request<{count:number}>('/account/unread-count'),
  agentOverview:()=>request<AgentOverview>('/agent/overview'),
  agentProperties:()=>request<{items:ManagedProperty[]}>('/agent/properties'),
  createProperty:(data:Record<string,unknown>)=>request<{property:ManagedProperty}>('/agent/properties',{method:'POST',body:JSON.stringify(data)}),
  updateProperty:(id:number,data:Record<string,unknown>)=>request<{property:ManagedProperty}>(`/agent/properties/${id}`,{method:'PATCH',body:JSON.stringify(data)}),
  deleteProperty:(id:number)=>request<void>(`/agent/properties/${id}`,{method:'DELETE'}),
  agentInquiries:()=>request<{items:Inquiry[]}>('/agent/inquiries'),
  markInquiry:(id:number,isRead=true)=>request<{isRead:boolean}>(`/agent/inquiries/${id}`,{method:'PATCH',body:JSON.stringify({isRead})}),
  adminOverview:()=>request<AdminOverview>('/admin/overview'),
  adminUsers:()=>request<{items:AdminUser[]}>('/admin/users'),
  updateUser:(id:number,data:{isActive?:boolean;role?:'user'|'agent'})=>request<{user:AdminUser}>(`/admin/users/${id}`,{method:'PATCH',body:JSON.stringify(data)}),
  adminProperties:()=>request<{items:(ManagedProperty&{agent:User})[]}>('/admin/properties'),
  adminApplications:()=>request<{items:AgentApplication[]}>('/admin/agent-applications'),
  reviewApplication:(id:number,status:'approved'|'rejected')=>request<{status:string}>(`/admin/agent-applications/${id}`,{method:'PATCH',body:JSON.stringify({status})}),
  breakdown:(city='')=>request<MarketBreakdown>(`/market/breakdown${city?`?city=${encodeURIComponent(city)}`:''}`),
  cv:async(id:number)=>{const response=await fetch(`${API_URL}/admin/agent-applications/${id}/cv`,{headers:{Authorization:`Bearer ${localStorage.getItem('accessToken')}`}});if(!response.ok)throw new ApiError('Unable to open CV.',response.status);return response.blob()},
}
interface AuthResult{user:User;accessToken:string;refreshToken:string}
export interface MarketStats{totalListings:number;averagePrice:number;averageArea:number;averagePricePerSqm:number;forSale:number;forRent:number;mostCommonType:string;mostActiveLocation:string;cities:string[]}
export interface TrendResult{city:string;series:{year:number;averagePricePerSqm:number}[];disclaimer:string}
export interface ManagedProperty extends Property{status:'draft'|'active'|'archived';views:number;createdAt:string}
export interface AgentOverview{totalListings:number;activeListings:number;totalViews:number;inquiries:number;unreadInquiries:number;recentProperties:ManagedProperty[]}
export interface Inquiry{id:number;message:string;isRead:boolean;createdAt:string;sender:User;property:Property}
export interface AdminOverview{totalUsers:number;totalAgents:number;totalListings:number;pendingApplications:number;recentProperties:(Property&{createdAt:string;agent:User})[]}
export interface AdminUser extends User{isActive:boolean;createdAt:string}
export interface AgentApplication{id:number;fullName:string;email:string;phone:string;city:string;agencyName?:string;experience?:string;message:string;status:'pending'|'approved'|'rejected';createdAt:string;cvUrl?:string;cvName?:string;user:User}
export interface ConversationMessage{id:number;body:string;senderId:number;createdAt:string;isRead:boolean}
export interface Conversation{id:number;user:User;agent:User;property:Property;lastMessage:string;lastMessageAt:string;unread:number;messages?:ConversationMessage[]}
export interface MarketBreakdown{city:string;total:number;propertyTypes:{type:string;count:number;share:number;averagePrice:number;averagePricePerSqm:number}[];purposes:{purpose:string;count:number;share:number}[]}
export {API_URL}
