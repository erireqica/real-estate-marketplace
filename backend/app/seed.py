from datetime import datetime, timedelta, timezone
import re
import unicodedata

from .extensions import db
from .models import (
    Amenity,
    AgentApplication,
    ApplicationStatus,
    Conversation,
    ConversationMessage,
    Favorite,
    ListingPurpose,
    Property,
    PropertyAmenity,
    PropertyImage,
    PropertyType,
    User,
    UserRole,
)


DEMO_DOMAIN = "@havenly.test"
DEMO_PASSWORD = "Password123!"

USERS = [
    ("admin@havenly.test", "Elira", "Berisha", UserRole.ADMIN, "+383 44 700 001", None),
    ("agent@havenly.test", "Arben", "Krasniqi", UserRole.AGENT, "+383 44 700 101", "North & Stone"),
    ("drita@havenly.test", "Drita", "Gashi", UserRole.AGENT, "+383 44 700 102", "Forma Properties"),
    ("valon@havenly.test", "Valon", "Rexhepi", UserRole.AGENT, "+383 44 700 103", "Urban Key"),
    ("nora@havenly.test", "Nora", "Bytyqi", UserRole.AGENT, "+383 44 700 104", "Lumi Homes"),
    ("leon@havenly.test", "Leon", "Dervishi", UserRole.AGENT, "+383 44 700 105", "Dervishi Property Studio"),
    ("user@havenly.test", "Luan", "Hoxha", UserRole.USER, "+383 44 710 201", None),
    ("mira@havenly.test", "Mira", "Selmani", UserRole.USER, "+383 44 710 202", None),
    ("besnik@havenly.test", "Besnik", "Morina", UserRole.USER, "+383 44 710 203", None),
    ("arta@havenly.test", "Arta", "Hasani", UserRole.USER, "+383 44 710 204", None),
    ("applicant@havenly.test", "Era", "Shala", UserRole.USER, "+383 44 720 301", None),
    ("rejected@havenly.test", "Ilir", "Miftari", UserRole.USER, "+383 44 720 302", None),
]

AMENITIES = (
    "Balcony", "Parking", "Elevator", "Air conditioning", "Furnished",
    "Garden", "Storage", "Central heating", "Security system", "Terrace",
    "Accessible entrance", "Electric vehicle charging",
)

# Covers remain first. A representative subset includes lightweight galleries so
# cards stay concise while property-detail thumbnails are demonstrated naturally.
# Every URL was checked against Unsplash when this dataset was assembled.
IMAGE_SETS = [
    ("photo-1600607687920-4e2a09cf159d", "photo-1505693416388-ac5ce068fe85", "photo-1618221195710-dd6b41faaea6"),
    ("photo-1600566753190-17f0baa2a6c3", "photo-1613490493576-7fde63acd811", "photo-1613977257363-707ba9348227", "photo-1613545325278-f24b0cae1224", "photo-1613977257592-4871e5fcd7c4"),
    ("photo-1600585154340-be6161a56a0c", "photo-1615874959474-d609969a20ed", "photo-1616486338812-3dadae4b4ace"),
    ("photo-1497366754035-f200968a6e72", "photo-1497366811353-6870744d04b2", "photo-1497366216548-37526070297c"),
    ("photo-1600047509807-ba8f99d2cdde",),
    ("photo-1600607687939-ce8a6c25118c",),
    ("photo-1600573472592-401b489a3cdc",),
    ("photo-1600566753086-00f18fb6b3ea",),
    ("photo-1500530855697-b586d89ba3ee",),
    ("photo-1600210492486-724fe5c67fb0", "photo-1564013799919-ab600027ffc6", "photo-1570129477492-45c003edd2be", "photo-1568605114967-8130f3a36994"),
    ("photo-1600566753051-f0b89df2dd90",),
    ("photo-1600566752355-35792bedcfea", "photo-1617104551722-3b2d51366400", "photo-1615529162924-f8605388461d"),
    ("photo-1600585154526-990dced4db0d",),
    ("photo-1497366412874-3415097a27e7",),
    ("photo-1600607688960-e095ff83135c",),
    ("photo-1512917774080-9991f1c4c750",),
    ("photo-1600573472550-8090b5e0745e",),
    ("photo-1600210491369-e753d80a41f3",),
    ("photo-1524758631624-e2822e304c36",),
    ("photo-1600047509358-9dc75507daeb", "photo-1600047508788-786f3865b4b9", "photo-1494526585095-c41746248156", "photo-1600585152915-d208bec867a1"),
    ("photo-1502672260266-1c1ef2d93688", "photo-1560185007-c5ca9d2c014d", "photo-1618220179428-22790b461013"),
    ("photo-1617806118233-18e1de247200",),
    ("photo-1556761175-b413da4baf72", "photo-1556761175-5973dc0f32e7", "photo-1536376072261-38c75010e6c9"),
    ("photo-1473448912268-2022ce9509d8",),
    ("photo-1616594039964-ae9021a400a0",),
    ("photo-1600585154363-67eb9e2e2099",),
    ("photo-1600210491892-03d54c0aaf87",),
    ("photo-1486406146926-c627a92ad1ab",),
]

LISTINGS = [
    # title, city, address, price, purpose, type, beds, baths, area, agent, amenities
    ("Light-filled apartment in Arbëria", "Prishtina", "Arbëria", 189000, "sale", "apartment", 3, 2, 128, "agent@havenly.test", ("Balcony", "Parking", "Elevator")),
    ("Contemporary villa with private garden", "Prishtina", "Marigona Residence", 465000, "sale", "villa", 4, 3, 310, "drita@havenly.test", ("Garden", "Parking", "Security system")),
    ("Penthouse above the city", "Prishtina", "Mati 1", 2100, "rent", "apartment", 3, 2, 176, "valon@havenly.test", ("Terrace", "Elevator", "Furnished")),
    ("Flexible office in the business district", "Prishtina", "Lakrishtë", 2800, "rent", "commercial", 0, 2, 210, "nora@havenly.test", ("Parking", "Elevator", "Accessible entrance")),
    ("Warm one-bedroom near the centre", "Prishtina", "Ulpiana", 620, "rent", "apartment", 1, 1, 58, "agent@havenly.test", ("Furnished", "Central heating", "Balcony")),
    ("Family house on a quiet residential street", "Prishtina", "Veternik", 298000, "sale", "house", 4, 3, 260, "drita@havenly.test", ("Garden", "Parking", "Storage")),
    ("Compact studio close to the university", "Prishtina", "Kodra e Diellit", 430, "rent", "apartment", 0, 1, 38, "valon@havenly.test", ("Furnished", "Elevator", "Central heating")),
    ("Corner retail unit with broad frontage", "Prishtina", "Bregu i Diellit", 174000, "sale", "commercial", 0, 1, 118, "nora@havenly.test", ("Parking", "Storage", "Accessible entrance")),
    ("Development parcel near the ring road", "Prishtina", "Çagllavicë", 220000, "sale", "land", None, None, 920, "leon@havenly.test", ("Accessible entrance",)),
    ("Old town residence with character", "Prizren", "Shadërvan", 240000, "sale", "house", 4, 2, 220, "agent@havenly.test", ("Terrace", "Storage", "Central heating")),
    ("Riverside family house", "Prizren", "Bazhdarhane", 198000, "sale", "house", 3, 2, 188, "drita@havenly.test", ("Garden", "Parking", "Balcony")),
    ("Renovated apartment by the old bridge", "Prizren", "Ortakoll", 94000, "sale", "apartment", 2, 1, 76, "valon@havenly.test", ("Balcony", "Air conditioning", "Storage")),
    ("Furnished loft overlooking the fortress", "Prizren", "Marash", 690, "rent", "apartment", 1, 1, 64, "nora@havenly.test", ("Furnished", "Air conditioning", "Terrace")),
    ("Ground-floor workspace near the centre", "Prizren", "Jeni Mahallë", 980, "rent", "commercial", 0, 1, 102, "leon@havenly.test", ("Accessible entrance", "Air conditioning", "Storage")),
    ("Quiet two-bedroom city retreat", "Peja", "City Centre", 780, "rent", "apartment", 2, 1, 92, "agent@havenly.test", ("Balcony", "Furnished", "Elevator")),
    ("Garden villa with mountain views", "Peja", "Kapeshnica", 335000, "sale", "villa", 4, 3, 280, "drita@havenly.test", ("Garden", "Parking", "Terrace")),
    ("Stone house near the Rugova road", "Peja", "Zatra", 176000, "sale", "house", 3, 2, 164, "valon@havenly.test", ("Garden", "Storage", "Central heating")),
    ("Modern apartment with mountain outlook", "Peja", "Dardania", 118000, "sale", "apartment", 2, 2, 104, "nora@havenly.test", ("Balcony", "Parking", "Elevator")),
    ("Serviced office for a small team", "Peja", "City Centre", 720, "rent", "commercial", 0, 1, 74, "leon@havenly.test", ("Furnished", "Air conditioning", "Accessible entrance")),
    ("Architect-designed family home", "Ferizaj", "Varosh", 275000, "sale", "house", 4, 3, 245, "agent@havenly.test", ("Garden", "Parking", "Security system")),
    ("New apartment near the city park", "Ferizaj", "Qendër", 105000, "sale", "apartment", 2, 1, 86, "drita@havenly.test", ("Balcony", "Elevator", "Central heating")),
    ("Bright rental with a generous balcony", "Ferizaj", "Dardania", 560, "rent", "apartment", 2, 1, 82, "valon@havenly.test", ("Balcony", "Furnished", "Parking")),
    ("Warehouse and office close to the highway", "Ferizaj", "Prelez", 3200, "rent", "commercial", 0, 2, 480, "nora@havenly.test", ("Parking", "Storage", "Security system")),
    ("Build-ready residential plot", "Ferizaj", "Talinnoc", 86000, "sale", "land", None, None, 610, "leon@havenly.test", ("Accessible entrance",)),
    ("Minimal apartment near the park", "Gjilan", "Dardania", 112000, "sale", "apartment", 2, 1, 84, "agent@havenly.test", ("Balcony", "Elevator", "Parking")),
    ("Three-bedroom home with courtyard", "Gjilan", "Arbëria", 164000, "sale", "house", 3, 2, 178, "drita@havenly.test", ("Garden", "Parking", "Storage")),
    ("Central apartment for long-term rent", "Gjilan", "Qendër", 510, "rent", "apartment", 2, 1, 79, "valon@havenly.test", ("Furnished", "Central heating", "Balcony")),
    ("Street-facing shop in a busy district", "Gjilan", "Bulevardi i Pavarësisë", 1250, "rent", "commercial", 0, 1, 96, "nora@havenly.test", ("Air conditioning", "Security system", "Accessible entrance")),
]

FAVORITES = {
    "user@havenly.test": (0, 1, 9, 15, 24),
    "mira@havenly.test": (2, 4, 11, 17, 20, 26),
    "besnik@havenly.test": (5, 8, 10, 16, 23),
    "arta@havenly.test": (3, 6, 13, 18, 22, 27),
}

CONVERSATIONS = [
    ("user@havenly.test", 0, [
        ("user", "Hello, is the Arbëria apartment still available, and does the parking space belong to the title?", True),
        ("agent", "It is available. One covered parking space is included in the ownership documents.", True),
        ("user", "Great. Could I see it on Saturday morning?", True),
        ("agent", "Yes—10:30 on Saturday works. I can meet you at the main entrance.", False),
    ]),
    ("user@havenly.test", 15, [
        ("user", "Does the Peja villa have year-round road access during winter?", True),
        ("agent", "Yes, the road is maintained throughout winter and the driveway is paved.", True),
        ("user", "Thank you. Is the garden included within the registered parcel boundary?", False),
    ]),
    ("mira@havenly.test", 2, [
        ("user", "I am looking for a six-month rental. Would the owner consider that term for the Mati penthouse?", True),
        ("agent", "The preferred term is twelve months, but six months could be considered with rent paid quarterly.", True),
        ("user", "That could work. Are utilities and building maintenance separate?", True),
        ("agent", "Utilities are separate; the monthly building fee is included in the advertised rent.", False),
        ("user", "Perfect, please send me two possible viewing times next week.", False),
    ]),
    ("mira@havenly.test", 11, [
        ("user", "Has the Ortakoll apartment renovation included the electrical wiring and plumbing?", True),
        ("agent", "Yes, both systems were replaced in 2023, along with the kitchen and bathroom.", True),
        ("user", "Do you have invoices or warranties available to review?", False),
    ]),
    ("besnik@havenly.test", 5, [
        ("user", "Could you confirm the Veternik house plot size and whether the lower level is registered?", True),
        ("agent", "The parcel is 4.2 ari, and all three levels appear in the cadastral extract.", True),
        ("user", "I would like to review the extract before arranging a second visit.", True),
        ("agent", "Of course. I will have a copy ready at our office tomorrow afternoon.", True),
    ]),
    ("besnik@havenly.test", 8, [
        ("user", "Is the Çagllavicë parcel connected to water and electricity at the boundary?", True),
        ("agent", "Electricity is at the road; the municipal water connection is approximately 40 metres away.", True),
        ("user", "Is residential construction permitted under the current plan?", False),
        ("agent", "The planning note indicates residential use, but buyers should confirm the final conditions with the municipality.", False),
    ]),
    ("arta@havenly.test", 20, [
        ("user", "Is the Ferizaj apartment ready to occupy, or are any finishing works outstanding?", True),
        ("agent", "It is complete and ready to occupy. Only the buyer's choice of light fixtures remains optional.", True),
        ("user", "Could we arrange a weekday viewing after 17:00?", True),
        ("agent", "Thursday at 17:30 is available. Shall I reserve that time for you?", False),
    ]),
    ("arta@havenly.test", 27, [
        ("user", "For the Gjilan shop, is exterior signage allowed above the street frontage?", True),
        ("agent", "Yes, subject to the building's standard size guidelines and municipal approval.", True),
        ("user", "What is the minimum lease term and deposit?", False),
        ("agent", "The minimum term is one year, with a two-month security deposit.", False),
        ("user", "Thanks. I will discuss the terms with my business partner and respond tomorrow.", False),
    ]),
    ("besnik@havenly.test", 9, [
        ("user", "Are the original stone features in the Shadërvan house protected, or can the interior layout be adapted?", True),
        ("agent", "The street facade should be preserved, while interior changes are possible subject to the usual municipal approval.", True),
        ("user", "Understood. Is there vehicle access to the property, or only pedestrian access through the old town?", False),
    ]),
]


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def clear_existing_demo_data():
    demo_user_ids = db.session.scalars(
        db.select(User.id).where(User.email.like(f"%{DEMO_DOMAIN}"))
    ).all()
    if not demo_user_ids:
        return
    property_ids = db.session.scalars(
        db.select(Property.id).where(Property.agent_id.in_(demo_user_ids))
    ).all()
    conversation_ids = db.session.scalars(
        db.select(Conversation.id).where(
            (Conversation.user_id.in_(demo_user_ids)) | (Conversation.agent_id.in_(demo_user_ids))
        )
    ).all()
    if conversation_ids:
        db.session.execute(db.delete(ConversationMessage).where(ConversationMessage.conversation_id.in_(conversation_ids)))
        db.session.execute(db.delete(Conversation).where(Conversation.id.in_(conversation_ids)))
    db.session.execute(db.delete(AgentApplication).where(AgentApplication.user_id.in_(demo_user_ids)))
    db.session.execute(db.delete(Favorite).where(Favorite.user_id.in_(demo_user_ids)))
    if property_ids:
        db.session.execute(db.delete(Favorite).where(Favorite.property_id.in_(property_ids)))
        db.session.execute(db.delete(PropertyAmenity).where(PropertyAmenity.property_id.in_(property_ids)))
        db.session.execute(db.delete(PropertyImage).where(PropertyImage.property_id.in_(property_ids)))
        db.session.execute(db.delete(Property).where(Property.id.in_(property_ids)))
    db.session.execute(db.delete(User).where(User.id.in_(demo_user_ids)))
    db.session.flush()


def make_user(email, first, last, role, phone, agency_name):
    user = User(
        email=email, first_name=first, last_name=last, role=role,
        phone=phone, agency_name=agency_name,
    )
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    return user


def seed_database():
    try:
        clear_existing_demo_data()
        now = datetime.now(timezone.utc)
        users = {}
        for index, user_data in enumerate(USERS):
            user = make_user(*user_data)
            user.created_at = now - timedelta(days=90 - index * 3)
            users[user.email] = user
        db.session.flush()

        amenities = {}
        for name in AMENITIES:
            amenity = db.session.scalar(db.select(Amenity).where(Amenity.slug == slugify(name)))
            if not amenity:
                amenity = Amenity(name=name, slug=slugify(name))
                db.session.add(amenity)
            amenities[name] = amenity
        db.session.flush()

        properties = []
        for index, listing in enumerate(LISTINGS):
            title, city, address, price, purpose, kind, beds, baths, area, agent_email, amenity_names = listing
            item = Property(
                agent_id=users[agent_email].id,
                title=title,
                slug=slugify(title),
                description=(
                    f"A carefully presented {kind} in {address}, {city}, with practical spaces "
                    "and a considered layout. The listing details are fictional demonstration data "
                    "created to show a realistic property-search and enquiry experience."
                ),
                price=price,
                purpose=ListingPurpose(purpose),
                property_type=PropertyType(kind),
                city=city,
                address=address,
                bedrooms=beds,
                bathrooms=baths,
                area_sqm=area,
                parking_spaces=0 if kind == "land" else (2 if kind in ("house", "villa") else index % 2),
                floor=(index % 8) + 1 if kind in ("apartment", "commercial") else None,
                year_built=None if kind == "land" else 2006 + (index % 19),
                views=96 + index * 41,
                is_featured=index in (0, 1, 9, 15, 20, 24),
                created_at=now - timedelta(days=index % 12, hours=index % 7),
            )
            item.amenities = [amenities[name] for name in amenity_names]
            db.session.add(item)
            db.session.flush()
            for position, image_id in enumerate(IMAGE_SETS[index]):
                db.session.add(PropertyImage(
                    property_id=item.id,
                    url=f"https://images.unsplash.com/{image_id}?auto=format&fit=crop&w=1400&q=85",
                    position=position,
                    alt_text=f"{title} demonstration listing image {position + 1}",
                ))
            properties.append(item)

        for email, property_indexes in FAVORITES.items():
            for offset, property_index in enumerate(property_indexes):
                db.session.add(Favorite(
                    user_id=users[email].id,
                    property_id=properties[property_index].id,
                    created_at=now - timedelta(days=offset + 1),
                ))

        for conversation_index, (user_email, property_index, messages) in enumerate(CONVERSATIONS):
            property_item = properties[property_index]
            started = now - timedelta(days=8 - conversation_index)
            conversation = Conversation(
                user_id=users[user_email].id,
                agent_id=property_item.agent_id,
                property_id=property_item.id,
                created_at=started,
                updated_at=started + timedelta(hours=len(messages)),
            )
            db.session.add(conversation)
            db.session.flush()
            for message_index, (sender, body, is_read) in enumerate(messages):
                db.session.add(ConversationMessage(
                    conversation_id=conversation.id,
                    sender_id=users[user_email].id if sender == "user" else property_item.agent_id,
                    body=body,
                    is_read=is_read,
                    created_at=started + timedelta(hours=message_index * 3),
                ))

        admin = users["admin@havenly.test"]
        applications = [
            ("applicant@havenly.test", "Prishtina", "Independent", "Four years in residential leasing", "I focus on clear communication and helping renters compare homes confidently.", ApplicationStatus.PENDING, None),
            ("leon@havenly.test", "Ferizaj", "Dervishi Property Studio", "Six years in residential and land sales", "I want to bring structured listing preparation and responsive buyer support to the platform.", ApplicationStatus.APPROVED, admin.id),
            ("rejected@havenly.test", "Gjilan", None, "Early-career property enthusiast", "I am building experience and would like to learn more about professional property representation.", ApplicationStatus.REJECTED, admin.id),
        ]
        for index, (email, city, agency, experience, message, status, reviewer) in enumerate(applications):
            applicant = users[email]
            db.session.add(AgentApplication(
                user_id=applicant.id,
                full_name=applicant.full_name,
                email=applicant.email,
                phone=applicant.phone,
                city=city,
                agency_name=agency,
                experience=experience,
                message=message,
                status=status,
                reviewed_by_id=reviewer,
                created_at=now - timedelta(days=12 - index * 3),
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
