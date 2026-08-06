import { Bath, BedDouble, Heart, MapPin, MoveUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type { Property } from '../../types'

export function PropertyCard({property,onUnsave}:{property:Property;onUnsave?:(id:number)=>void}){
  const auth=useAuth();const saved=auth.savedIds.has(property.id)
  const price=new Intl.NumberFormat('en-US',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(property.price)
  async function toggle(event:React.MouseEvent){event.preventDefault();if(!auth.user){auth.openAuth();return}const next=await auth.toggleFavorite(property.id);if(!next)onUnsave?.(property.id)}
  return <article className="property-card"><Link to={`/properties/${property.slug}`} className="property-image"><img src={property.imageUrl || 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1000&q=80'} alt={property.title}/><span className="pill">For {property.purpose}</span><button aria-label={saved?'Remove saved property':'Save property'} onClick={toggle}><Heart size={19} fill={saved?'currentColor':'none'}/></button></Link><div className="property-copy"><div className="property-price">{price}{property.purpose==='rent'&&<small>/month</small>}</div><Link to={`/properties/${property.slug}`}><h3>{property.title}</h3></Link><p><MapPin size={15}/>{property.address}, {property.city}</p><div className="specs"><span><BedDouble/> {property.bedrooms ?? '—'} Beds</span><span><Bath/> {property.bathrooms ?? '—'} Baths</span><span>{property.areaSqm} m²</span><MoveUpRight className="card-arrow"/></div></div></article>
}
