from .extensions import db
from .models import Amenity, AgentApplication, ApplicationStatus, Conversation, ConversationMessage, Favorite, ListingPurpose, Property, PropertyImage, PropertyType, User, UserRole

IMAGES = [
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=85",
]
LISTINGS = [
    ("Light-filled apartment in Arbëria", "Prishtina", "Arbëria", 189000, "sale", "apartment", 3, 2, 128),
    ("Contemporary villa with private garden", "Prishtina", "Marigona Residence", 465000, "sale", "villa", 4, 3, 310),
    ("Old town residence with character", "Prizren", "Shadërvan", 240000, "sale", "house", 4, 2, 220),
    ("Quiet two-bedroom city retreat", "Peja", "City Centre", 780, "rent", "apartment", 2, 1, 92),
    ("Architect-designed family home", "Ferizaj", "Varosh", 275000, "sale", "house", 4, 3, 245),
    ("Penthouse above the city", "Prishtina", "Mati 1", 2100, "rent", "apartment", 3, 2, 176),
    ("Street-level studio for modern retail", "Prishtina", "Bregu i Diellit", 1650, "rent", "commercial", 0, 1, 135),
    ("Riverside family house", "Prizren", "Bazhdarhane", 198000, "sale", "house", 3, 2, 188),
    ("Minimal apartment near the park", "Gjilan", "Dardania", 112000, "sale", "apartment", 2, 1, 84),
    ("Garden villa with mountain views", "Peja", "Kapeshnica", 335000, "sale", "villa", 4, 3, 280),
    ("Flexible office in the business district", "Prishtina", "Lakrishtë", 2800, "rent", "commercial", 0, 2, 210),
    ("Warm one-bedroom near the centre", "Prishtina", "Ulpiana", 620, "rent", "apartment", 1, 1, 58),
]


def make_user(email, first, last, role, password="Password123!"):
    user = User(email=email, first_name=first, last_name=last, role=role, phone="+383 44 555 010")
    user.set_password(password); db.session.add(user); return user


def seed_database():
    if db.session.scalar(db.select(User).limit(1)): return
    admin = make_user("admin@havenly.test", "Elira", "Berisha", UserRole.ADMIN)
    agent1 = make_user("agent@havenly.test", "Arben", "Krasniqi", UserRole.AGENT); agent1.agency_name = "North & Stone"
    agent2 = make_user("drita@havenly.test", "Drita", "Gashi", UserRole.AGENT); agent2.agency_name = "Forma Properties"
    user = make_user("user@havenly.test", "Luan", "Hoxha", UserRole.USER)
    applicant = make_user("applicant@havenly.test", "Era", "Shala", UserRole.USER)
    amenities = [Amenity(name=name, slug=name.lower().replace(" ", "-")) for name in ("Balcony", "Parking", "Elevator", "Air conditioning", "Furnished", "Garden")]
    db.session.add_all(amenities); db.session.flush()
    properties = []
    for i, (title, city, address, price, purpose, kind, beds, baths, area) in enumerate(LISTINGS):
        item = Property(agent_id=(agent1 if i % 2 == 0 else agent2).id, title=title, slug=title.lower().replace(" ", "-").replace("ë", "e"), description="A considered property offering generous natural light, practical living spaces and a strong connection to its surroundings. Carefully maintained and ready for its next chapter.", price=price, purpose=ListingPurpose(purpose), property_type=PropertyType(kind), city=city, address=address, bedrooms=beds, bathrooms=baths, area_sqm=area, parking_spaces=1 if i % 3 else 2, floor=(i % 7)+1 if kind in ("apartment", "commercial") else None, year_built=2010+i, views=84+i*37, is_featured=i<3)
        item.amenities = amenities[i%3:i%3+3]
        db.session.add(item); db.session.flush()
        db.session.add_all([PropertyImage(property_id=item.id, url=IMAGES[(i+j)%len(IMAGES)], position=j, alt_text=title) for j in range(3)])
        properties.append(item)
    db.session.add(AgentApplication(user_id=applicant.id, full_name=applicant.full_name, email=applicant.email, phone=applicant.phone, city="Prishtina", experience="Three years in residential sales", message="I would like to bring my growing client network and a thoughtful approach to Havenly.", status=ApplicationStatus.PENDING))
    db.session.add_all([Favorite(user_id=user.id, property_id=properties[0].id), Favorite(user_id=user.id, property_id=properties[2].id)])
    conversation = Conversation(user_id=user.id, agent_id=agent1.id, property_id=properties[0].id)
    db.session.add(conversation); db.session.flush()
    db.session.add_all([ConversationMessage(conversation_id=conversation.id, sender_id=user.id, body="Is this home available for a viewing this weekend?", is_read=True), ConversationMessage(conversation_id=conversation.id, sender_id=agent1.id, body="Yes, it is available Saturday afternoon. Would 14:00 work for you?", is_read=False)])
    db.session.commit()
