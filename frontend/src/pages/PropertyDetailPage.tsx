import { Bath, BedDouble, Calendar, Car, Check, Heart, MapPin, Maximize, Send } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import type { Property } from '../types'

export function PropertyDetailPage(){
  const {slug}=useParams()
  const auth=useAuth()
  const [property,setProperty]=useState<Property>()
  const [active,setActive]=useState(0)
  const [feedback,setFeedback]=useState('')
  useEffect(()=>{if(slug)api.property(slug).then(r=>setProperty(r.property))},[slug])
  if(!property)return <div className="empty page-state">Loading property…</div>
  const images=property.images?.length?property.images:[{id:0,url:property.imageUrl??'',altText:property.title}]
  async function inquire(form:FormData){
    if(!auth.user){auth.openAuth();return}
    try{const result=await api.inquiry(property!.id,String(form.get('message')));setFeedback(result.message)}
    catch(error){setFeedback(error instanceof Error?error.message:'Unable to send inquiry.')}
  }
  const saved=auth.savedIds.has(property.id)
  async function toggleSave(){
    if(!auth.user){auth.openAuth();return}
    try{const next=await auth.toggleFavorite(property!.id);setFeedback(next?'Property saved to your profile.':'Removed from saved properties.')}
    catch(error){setFeedback(error instanceof Error?error.message:'Unable to update saved properties.')}
  }
  return <div className="detail-page">
    <section className="gallery">
      <div className="gallery-main"><img src={images[active].url} alt={images[active].altText}/><span className="pill">For {property.purpose}</span></div>
      <div className="gallery-thumbs">{images.map((image,index)=><button className={index===active?'active':''} onClick={()=>setActive(index)} key={image.id}><img src={image.url} alt=""/></button>)}</div>
    </section>
    <section className="detail-grid"><div>
      <div className="detail-heading"><div><p className="eyebrow green">{property.propertyType}</p><h1>{property.title}</h1><p><MapPin/> {property.address}, {property.city}</p></div><div className="detail-price-actions"><div className="detail-price"><strong>€{property.price.toLocaleString()}</strong>{property.purpose==='rent'&&<span>/ month</span>}</div><button className={`save-button ${saved?'saved':''}`} onClick={toggleSave}><Heart fill={saved?'currentColor':'none'}/> {saved?'Saved':'Save'}</button></div></div>
      <div className="detail-specs">
        <span><BedDouble/>{property.bedrooms??'—'}<small>Bedrooms</small></span>
        <span><Bath/>{property.bathrooms??'—'}<small>Bathrooms</small></span>
        <span><Maximize/>{property.areaSqm}<small>m² area</small></span>
        {property.parkingSpaces!=null&&property.parkingSpaces>0&&<span><Car/>{property.parkingSpaces}<small>Parking</small></span>}
        {property.yearBuilt!=null&&property.yearBuilt>0&&<span><Calendar/>{property.yearBuilt}<small>Built</small></span>}
      </div>
      <div className="detail-copy"><h2>About this property</h2><p>{property.description}</p><h2>Amenities</h2><div className="amenities">{property.amenities?.map(item=><span key={item}><Check/> {item}</span>)}</div></div>
    </div><aside className="agent-card"><p className="eyebrow green">LISTING AGENT</p><div className="agent-identity"><div className="avatar">{property.agent?.firstName[0]}{property.agent?.lastName[0]}</div><div><h3>{property.agent?.fullName}</h3><p>{property.agent?.agencyName||'Independent agent'}</p></div></div><p>Interested in this property? Send a message directly to the listing agent.</p><form action={inquire}><textarea name="message" required minLength={10} placeholder="Hello, is this property still available?"/><button className="primary-button"><Send/> Send inquiry</button></form>{feedback&&<div className="form-feedback">{feedback}</div>}</aside></section>
  </div>
}
