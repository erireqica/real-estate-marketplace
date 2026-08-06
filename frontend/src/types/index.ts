export type Role = 'user' | 'agent' | 'admin'
export interface User { id:number; email:string; firstName:string; lastName:string; fullName:string; phone?:string; avatarUrl?:string; agencyName?:string; role:Role }
export type ListingPurpose = 'sale' | 'rent'
export type PropertyType = 'apartment'|'house'|'villa'|'commercial'|'land'
export interface Property { id:number; slug:string; title:string; price:number; purpose:ListingPurpose; propertyType:PropertyType; city:string; address:string; bedrooms?:number; bathrooms?:number; areaSqm:number; isFeatured:boolean; imageUrl?:string; description?:string; images?:{id:number;url:string;altText?:string}[]; amenities?:string[]; agent?:User; parkingSpaces?:number;floor?:number;yearBuilt?:number;views?:number }
export interface Paginated<T> { items:T[]; pagination:{page:number;pages:number;total:number} }
