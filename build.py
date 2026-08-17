#!/usr/bin/env python3
"""
Sky View Real Estate — static site builder.

Assembles every page from shared chrome (head/nav/footer) plus the data below,
and writes plain static HTML. There is no runtime build step: the output is
committed and can be served by any static host.

    python3 build.py

Everything a non-developer needs to change lives in CONFIG and the data blocks.
"""

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = ROOT

# ============================================================================
# CONFIG — edit these, rebuild, done.
# ============================================================================
CONFIG = {
    "name": "Sky View Real Estate",
    "legal": "Sky View Real Estate Brokers",
    "founded": "2005",  # NOTE: skyviewdubai.com says 2005 on most pages but 2006
                        # in the homepage sidebar. Confirm with the client.
    "phone_landline": "+971 4 437 0431",
    "phone_mobile": "+971 50 285 9321",
    "phone_pm": "+971 55 106 6856",
    "email": "info@skyviewdubai.com",
    "email_hr": "hr@skyviewdubai.com",
    "email_pm": "pm@skyviewdubai.com",
    "whatsapp": "971586693976",
    "hq": "Clover Bay Tower, Office 1108 &amp; 1109, Marasi Drive, Business Bay, Dubai",
    "branch": "Hessa 8, Shop #1, Hessa Street, Al Barsha Third, Dubai",
    "hours": "Sun – Fri · 9:00 AM – 6:00 PM",
    "showreel_video": "12Ql2-tztm8",  # "Why Pay Rent When You Can Own!" — their channel
    "showreel_title": "Why Pay Rent When You Can Own — Sky View Real Estate",

    # Where the contact + newsletter forms POST. Leave empty and the forms fall
    # back to opening a pre-filled WhatsApp message, so they still work today.
    # Set to a Formspree/Getform/own-API endpoint to collect submissions.
    "form_endpoint": "",

    # Analytics OFF by default on purpose: these are the LIVE property IDs from
    # skyviewdubai.com, and firing staging/demo traffic into a client's
    # production analytics corrupts their reporting. Flip to True only on the
    # real production deploy.
    "analytics_enabled": False,
    "ga4_id": "G-VFL778XHQY",
    "gtm_id": "GTM-WL937D6C",

    "social": {
        "Instagram": "https://www.instagram.com/skyviewdubai/",
        "LinkedIn": "https://www.linkedin.com/company/sky-view-real-estate-brokers/",
        "Facebook": "https://www.facebook.com/skyviewdubai/",
        "YouTube": "https://www.youtube.com/channel/UClfpPV9oaeYksVSZondiLnA",
        "X / Twitter": "https://twitter.com/skyview_re",
    },
}

WA_BASE = ("https://api.whatsapp.com/send?phone=" + CONFIG["whatsapp"] +
           "&text=I'm%20interested%20in%20Skyview%20Properties.%20Please%20send%20details%20"
           "on%20pricing%2C%20projects%20and%20availability.")

# ============================================================================
# LISTINGS — real properties scraped from skyviewdubai.com
# ============================================================================
LISTINGS = [
    {
        "slug": "genuine-motivated-seller-non-negotiable",
        "ref": "SkyView-35866",
        "title": "Genuine | Motivated Seller | Non Negotiable",
        "type": "Townhouse", "purpose": "Sale",
        "price": "AED 2,798,000", "price_note": "",
        "location": "DAMAC Islands › Bora Bora 2",
        "area_full": "Dubai › DAMAC Islands › Bora Bora › Bora Bora 2",
        "beds": 5, "baths": 6, "area": "2,459", "parking": 0,
        "img": "assets/p1.jpg",
        "agent": "Mayurakshi Singh", "agent_img": "assets/team-myra.jpg",
        "agent_phone": "971521024597",
        "desc": [
            "Sky View Real Estate Brokers is pleased to offer this 5 bedroom plus maid's corner townhouse in Bora Bora 2, located in DAMAC Islands.",
            "DAMAC Islands – Bora Bora 2 is a residential cluster within the DAMAC Islands project by DAMAC Properties. The concept is inspired by island resorts and is designed to create a private residential environment with resort-style infrastructure.",
            "The architectural concept combines contemporary forms, panoramic glazing and a light colour palette, with expressive vertical elements and open spaces.",
        ],
        "details": ["5 bedroom corner townhouse", "Maid's room with en-suite bathroom",
                    "1 laundry / storage area", "Ground plus first & second floor (G+2)",
                    "L-shaped garden"],
        "amenities": ["Aqua Park", "BBQ Area", "Beach Access", "Dining outlets", "Fitness Zone",
                      "Floating Deck With Sunbeds", "Fountain", "Gaming Lounge", "Gondola Paddling",
                      "Jogging Tracks", "Mini Golf", "Pet Garden"],
    },
    {
        "slug": "resale-high-floor-closed-kitchen-white-goods",
        "ref": "SkyView-35870",
        "title": "Resale | High Floor | Closed Kitchen | White Goods",
        "type": "Apartment", "purpose": "Sale",
        "price": "AED 1,880,000", "price_note": "",
        "location": "Majan › Tulip Oasis 10",
        "area_full": "Dubai › Majan › Tulip Oasis 10",
        "beds": 2, "baths": 3, "area": "1,514", "parking": 1,
        "img": "assets/p3.jpg",
        "agent": "Pratik Morjaria", "agent_img": "assets/team-pratik.jpg",
        "agent_phone": "971526920793",
        "desc": [
            "A high-floor two bedroom resale unit in Tulip Oasis 10, Majan, offered with a closed kitchen and white goods included.",
            "Majan sits within Dubai Land and has become one of the city's stronger value communities, with chiller-free buildings and competitive service charges.",
        ],
        "details": ["2 bedrooms", "Closed kitchen", "White goods included",
                    "High floor", "Allocated parking"],
        "amenities": ["Swimming Pool", "Gymnasium", "Covered Parking", "24/7 Security",
                      "Children's Play Area", "Landscaped Grounds"],
    },
    {
        "slug": "prime-location-spacious-2080-pp-handover-soon",
        "ref": "SkyView-35869",
        "title": "Prime Location | Spacious | 20/80 PP | Handover soon",
        "type": "Apartment", "purpose": "Sale",
        "price": "AED 1,830,000", "price_note": "",
        "location": "Majan › Tulip Oasis 11",
        "area_full": "Dubai › Majan › Tulip Oasis 11",
        "beds": 2, "baths": 3, "area": "2,038", "parking": 1,
        "img": "assets/p6.jpg",
        "agent": "Pavan Narayan", "agent_img": "assets/team-kadir.jpg",
        "agent_phone": "971581731943",
        "desc": [
            "A spacious two bedroom apartment in Tulip Oasis 11 offered on a 20/80 payment plan with handover approaching.",
            "The 20/80 structure means 20% is paid during construction and the remaining 80% on handover — a common entry point for investors targeting Majan's rental yields.",
        ],
        "details": ["2 bedrooms", "20/80 payment plan", "Handover soon",
                    "Spacious layout", "Prime location within the community"],
        "amenities": ["Swimming Pool", "Gymnasium", "Retail on Podium", "Covered Parking",
                      "24/7 Security", "Children's Play Area"],
    },
    {
        "slug": "chiller-free-low-floor-unfurnished-near-exit",
        "ref": "SkyView-35872",
        "title": "Chiller Free | Low Floor | Unfurnished | Near Exit",
        "type": "Apartment", "purpose": "Rent",
        "price": "AED 64,999", "price_note": "/yr",
        "location": "Jumeirah Village Circle › Botanica",
        "area_full": "Dubai › Jumeirah Village Circle › District 13 › Botanica",
        "beds": 1, "baths": 2, "area": "999", "parking": 1,
        "img": "assets/p4.jpg",
        "agent": "Muhammad Ahmad Khan", "agent_img": "assets/team-rahul.jpg",
        "agent_phone": "971586866804",
        "desc": [
            "A chiller-free one bedroom apartment in Botanica, District 13, Jumeirah Village Circle — unfurnished, low floor and positioned close to the community exit.",
            "Chiller-free means district cooling charges are included in the rent, which removes a significant variable cost for tenants.",
        ],
        "details": ["1 bedroom", "Chiller free", "Unfurnished", "Low floor",
                    "Close to community exit", "Allocated parking"],
        "amenities": ["Swimming Pool", "Gymnasium", "Covered Parking", "24/7 Security",
                      "Supermarket Nearby", "Landscaped Grounds"],
    },
    {
        "slug": "smart-unit-chiller-free-private-pool",
        "ref": "SkyView-35801",
        "title": "Smart Unit | Chiller-Free | Private Pool",
        "type": "Apartment", "purpose": "Sale",
        "price": "AED 1,670,000", "price_note": "",
        "location": "Dubai Land › Majan › Divine Al Barari",
        "area_full": "Dubai › Dubai Land › Majan › Divine Al Barari",
        "beds": 2, "baths": 2, "area": "1,115", "parking": 1,
        "img": "assets/p2.jpg",
        "agent": "Rohin Bhardwaj", "agent_img": "assets/team-doni.jpg",
        "agent_phone": "971526920793",
        "desc": [
            "A smart-home enabled two bedroom apartment at Divine Al Barari, Majan, with a private pool and chiller-free service.",
            "Divine Al Barari sits on the Majan edge of Dubai Land, within reach of Al Barari's greenery and the Sheikh Mohammed Bin Zayed Road corridor.",
        ],
        "details": ["2 bedrooms", "Smart home system", "Private pool",
                    "Chiller free", "Allocated parking"],
        "amenities": ["Private Pool", "Gymnasium", "Smart Home", "Covered Parking",
                      "24/7 Security", "Landscaped Grounds"],
    },
    {
        "slug": "5br-spacious-villa-premium-living-serro",
        "ref": "SkyView-35744",
        "title": "5BR Spacious Villa | Premium Living | Serro",
        "type": "Villa", "purpose": "Sale",
        "price": "AED 11,255,888", "price_note": "",
        "location": "The Heights Country Club & Wellness › Serro",
        "area_full": "Dubai › The Heights Country Club & Wellness › Serro",
        "beds": 5, "baths": 6, "area": "7,141", "parking": 2,
        "img": "assets/p5.jpg",
        "agent": "Manisha Sharma", "agent_img": "assets/team-bana.jpg",
        "agent_phone": "971521024597",
        "desc": [
            "A five bedroom villa at Serro, within The Heights Country Club & Wellness — one of Dubai's larger wellness-led master communities.",
            "At 7,141 sq.ft this is a premium family layout with generous reception space, a private garden and direct access to the club's sporting and wellness facilities.",
        ],
        "details": ["5 bedrooms", "6 bathrooms", "7,141 sq.ft built-up area",
                    "Private garden", "2 covered parking bays", "Country club access"],
        "amenities": ["Country Club", "Golf", "Wellness Centre", "Swimming Pools",
                      "Tennis Courts", "Jogging Tracks", "Retail & Dining", "24/7 Security"],
    },
]

# ============================================================================
# SERVICES — copy taken verbatim from the client's own service pages
# ============================================================================
SERVICES = [
    {
        "slug": "property-management",
        "title": "Property Management",
        "lede": "Owning a property as a landlord is great — until you start managing the issues that come with it.",
        "body": [
            "Owning a property as a landlord is awesome! Until you start managing the issues that come with it, like finding the right tenant or dealing with property maintenance on your own. Find out how your property can be professionally managed by our consultants to help optimise your financial investment, increase ROI and minimise risks involved.",
            "Sky View Real Estate Brokers will take care of it all. Right from creating the best visibility for your property, finding the right tenant, collecting the rent, carrying out regular inspections and taking care of the property maintenance to give you total peace of mind.",
            "Sky View provides a full range of services to make the lives of landlords much easier — from residential leasing, tenancy management, detailed pricing strategy and marketing of property to property handover, maintenance and inspections.",
            "Our agents are RERA-registered sales &amp; leasing consultants who share our vision and enthusiasm for Dubai's real estate market. We can manage from a single unit to an entire building.",
        ],
        "highlights": ["Currently managing over 100+ projects in Dubai",
                       "Dedicated property consultants to manage your account",
                       "Bespoke property management tailored to your needs"],
        "includes": ["Tenant Acquisition and Screening", "Lease Management", "Property Maintenance",
                     "Financial Management", "Legal Compliance", "Property Marketing"],
        "img": "assets/p6.jpg",
    },
    {
        "slug": "investment-consultancy",
        "title": "Investment Consultancy",
        "lede": "In-depth, sector-specific analysis of investment opportunities in the Dubai market.",
        "body": [
            "Our Investment Consultancy team assists customers by offering in-depth and sector-specific analysis about investment opportunities in the Dubai market. Our experts advise at various property acquisition stages — from identification and sourcing, due diligence and asset management through to negotiations.",
            "Over years of experience in the property market, and being property investors ourselves, we believe that no amount of time can be wasted in making sure our investors' decisions are right. We act as behind-the-scenes consultants by analysing market trends, visiting proposed projects, meeting real estate professionals and understanding the ever-changing legal aspects of real estate regulation.",
            "Our industry expertise and extensive research has earned clients ranging across builders, real estate investors and property developers. It does not matter if you are a new investor or an experienced one — Sky View has been managing all types of investment portfolios since inception.",
        ],
        "highlights": ["Choosing the right prime location", "Capital appreciation",
                       "Achieving maximum yields for your investments"],
        "includes": ["Choosing the Right Property", "Easy Payment Plans", "High Rental Returns",
                     "High Resell Value", "Maximum Capital Appreciation"],
        "img": "assets/dubai2.jpg",
    },
    {
        "slug": "developer-consultancy",
        "title": "Developer Consultancy",
        "lede": "Comprehensive feasibility studies and pre-development advice for developers and funding institutions.",
        "body": [
            "Sky View Real Estate Brokers' development consultancy services in Dubai provide a comprehensive feasibility study and pre-development advice with the right planning to stakeholders, developers and funding institutions for their commercial and residential projects across the region.",
            "In a place like Dubai where the potential of property development is endless, our in-house team of specialist consultants are ready to assist with in-depth understanding of market requirements, opportunities and trends, along with award-winning problem-solving strategies.",
            "Our development consultants understand the factors involved with project development and its hidden challenges, which at times are ignored or unknown. We ensure every aspect from project conception through completion is organised and well taken care of.",
        ],
        "highlights": ["Access to the latest market information",
                       "Awareness of socio-economic trends in Dubai real estate",
                       "End-to-end coverage from conception to completion"],
        "includes": ["Project Feasibility Study", "Choosing the Right Land", "Choosing the Developer",
                     "Preparation of Layout &amp; Plan", "Arranging Engineering Consultant",
                     "Marketing Material", "Launching &amp; Selling the Project"],
        "img": "assets/dubai8.jpg",
    },
    {
        "slug": "mortgage-advisory",
        "title": "Mortgage Advisory",
        "lede": "With 40+ banks offering mortgage products, professional advice makes the difference.",
        "body": [
            "It's important to have all things right when making a financial decision while getting a mortgage. If you are looking for mortgage advisory in Dubai, Sky View Real Estate Brokers are the right choice for you.",
            "With over 40 financial institutions and banks offering mortgage products of various kinds, it is hard for customers to make a good decision without seeking professional advice. We can make your mortgage selection and application process smooth and successful due to our in-depth knowledge and industry experience.",
            "Why rent, when you can own your property in Dubai? Market research says 79% of people believe that purchasing and owning property is better than paying rent year-round. Being a UAE resident, you can obtain financing up to 75% of the total property value based on your income eligibility.",
        ],
        "highlights": ["Re-mortgage options available", "New &amp; off-plan property mortgages",
                       "Mortgage options for previously owned Dubai properties"],
        "includes": ["Impartial Advice", "Pre-Approvals", "Property Dealing",
                     "Communications with Banks", "End to End Process Management",
                     "Initial Deal Assistance"],
        "img": "assets/p2.jpg",
    },
    {
        "slug": "why-invest-in-dubai",
        "title": "Why Invest in Dubai",
        "lede": "Constant economic growth, high rental values and property price appreciation.",
        "body": [
            "Being one of the most famous cities in the world, Dubai is a leading destination for real estate investment. Investors get a high rate of return due to constant economic growth, high property rental value and property price appreciation.",
            "Year-round, visitors flock from across the globe to Dubai for business, conferences, exhibitions, entertainment, shopping or family holidays, due to its tourism infrastructure — making it an ideal hub for property investment.",
            "Dubai has long been considered a haven for property investment due to its growing population and its role as home to thousands of foreign workers relocating for career growth, safety and global trade.",
        ],
        "highlights": ["High return on investment", "Lower pay-back period",
                       "Benefits whether you live in Dubai or abroad"],
        "includes": ["UAE's Stable Currency", "Tax Efficient", "Premium Healthcare",
                     "Dubai's Connectivity", "Strategic Location", "Priority on Safety",
                     "World Class Amenities", "Growing Population"],
        "img": "assets/dubai1.jpg",
    },
    {
        "slug": "management-services",
        "title": "Management Services",
        "lede": "Streamline your property management with a single accountable team.",
        "body": [
            "We ensure your property is occupied by reliable tenants through a thorough screening process, including background checks and financial assessments. From drafting leases to handling renewals, we manage all aspects of your rental agreements.",
            "Our team takes care of routine and emergency maintenance, handles rent collection, budgeting and financial reporting, and keeps you compliant with local laws and regulations.",
            "With over 15 years in the industry we tailor our services to your specific needs and goals, using technology to streamline processes and keep you informed and in control.",
        ],
        "highlights": ["Time savings", "Maximised returns", "Risk mitigation", "Peace of mind"],
        "includes": ["Tenant Acquisition and Screening", "Lease Management", "Property Maintenance",
                     "Financial Management", "Legal Compliance", "Property Marketing"],
        "img": "assets/p5.jpg",
    },
]

# ============================================================================
# TEAM — full roster from skyviewdubai.com/company/our-team
# ============================================================================
LEADERSHIP = [
    ("Ashok Kumar Kanjwani", "Chairman", "assets/team-ashok.jpg"),
    ("Akash Kanjwani", "Chief Executive Officer", "assets/team-akash.jpg"),
    ("Kangan Kanjwani", "Property Management Manager", "assets/team-kangan.jpg"),
    ("Rahul Tharwani", "Director of Sales", "assets/team-rahul.jpg"),
    ("Doni Mehta", "Director of Sales", "assets/team-doni.jpg"),
    ("Pratik Morjaria", "Development Manager", "assets/team-pratik.jpg"),
    ("Kadir Khan", "Associate Director", "assets/team-kadir.jpg"),
    ("Bana Koujan", "Associate Director", "assets/team-bana.jpg"),
    ("Myra Dacosta", "Senior Property Consultant", "assets/team-myra.jpg"),
]

ROSTER = [
    ("Directors &amp; Partners", [
        "Claudia Gomes — Director of Sales", "Yash Gajria — Senior Sales Manager",
        "Deepti Gurmukh — Senior Sales Manager", "Shilpa Serai — Sales Manager",
        "Manjit Kaur — Sales Manager", "Jayesh Mordani — Associate Partner",
        "Kerttu Jallai — Associate Partner",
    ]),
    ("Associate Directors", [
        "Ikhwak Singh", "Deepali Motiani", "Nihal Beserler", "Ashiq Kareem",
        "Akshay Sodhi", "Lina Abdalla", "Najed Hussain",
    ]),
    ("Senior Property Consultants", [
        "Brandon Lee Naidoo", "Laveena Udasi", "Firas Jadaan", "Runa Das",
        "Richard Andrew Crisp", "Laveesh Lilaramani", "Muhammad Ahmad Khan",
        "Javed Iqbal", "Sarabjeet Singh", "Rohin Bhardwaj", "Pavan Narayan",
        "Tanveer Hazarika", "Khanjan Gusani",
    ]),
    ("Property Consultants", [
        "Shivam Goswami", "Fatima Harris", "Biljana Tasic", "Emmanuel Furtado",
        "Ashish Guwalani", "Beena Chandarana", "Pedrito Dsilva", "Michelle Vanrooyen",
        "Mohammed Rayhan", "Rukshan Francis", "Darshan Yogesh Mistry", "Mansi Kaushik Vyas",
    ]),
    ("Investment Advisors", [
        "Ponnanna Kaveriappa", "Deepak Yadav", "Brisilda Selmani", "Leena Nankani",
        "Sheham Siddique", "Rohit Adnani", "Naeelah Vally", "Ainam Taslim Raza",
        "Devang Dattani",
    ]),
    ("Operations &amp; Support", [
        "Sheila Dsilva", "Julien Altom", "Nilesh Vyas", "Mark Calinawan",
        "Jevine Umahon", "Christine Mangua", "Mary Margaret Bornalo", "Junes Vayalil",
    ]),
]

# ============================================================================
# COMMUNITIES
# ============================================================================
COMMUNITIES = [
    ("Downtown Dubai", "Iconic · Central · Premium", "assets/dubai1.jpg"),
    ("Business Bay", "Waterfront · Connected · Urban", "assets/dubai2.jpg"),
    ("DAMAC Islands", "Resort · Lagoons · Family", "assets/p1.jpg"),
    ("Jumeirah Village Circle", "Value · Community · Chiller-free", "assets/dubai8.jpg"),
    ("Dubai Hills Estate", "Green · Golf · Established", "assets/dubai7.jpg"),
    ("Majan · Dubai Land", "Emerging · Payment plans · Yield", "assets/dubai3.jpg"),
]

# ============================================================================
# BLOG — real posts from skyviewdubai.com/blog
# ============================================================================
POSTS = [
    {
        "slug": "uae-market-2025", "date": "2025-09-19", "title": "The UAE Market in 2025",
        "sub": "Momentum, caution &amp; opportunity",
        "excerpt": "The real estate sector globally is going through a period of recalibration — and the UAE is no exception.",
        "img": "assets/dubai1.jpg",
        "body": [
            "The real estate sector globally is going through a period of recalibration. Interest rates, construction costs and buyer expectations have all shifted, and the UAE market has absorbed those changes differently to most.",
            "Momentum remains strong across Dubai's established communities, while newer master developments continue to attract off-plan demand on the back of extended payment plans.",
            "Caution is warranted in segments where supply is arriving quickly. Our advice to investors remains what it has always been: buy the community and the service charge, not just the headline yield.",
        ],
    },
    {
        "slug": "properties-in-dubai", "date": "2025-09-13", "title": "Properties in Dubai",
        "sub": "A world of opportunity",
        "excerpt": "Dubai has transformed into one of the most sought-after real estate destinations in the world.",
        "img": "assets/dubai5.jpg",
        "body": [
            "Dubai has transformed into one of the most sought-after real estate destinations in the world. From luxury waterfront residences to value-led communities, the range of stock available is unusually broad for a single city.",
            "Freehold ownership in designated areas, no annual property tax, and a residency pathway tied to qualifying investment continue to make the market attractive to overseas buyers.",
        ],
    },
    {
        "slug": "dubai-real-estate-market-2025", "date": "2025-09-11",
        "title": "Dubai Real Estate Market 2025", "sub": "Quick investor update",
        "excerpt": "Dubai's property market continues to shine in 2025 — prices, rental yields and transaction volumes.",
        "img": "assets/dubai3.jpg",
        "body": [
            "Dubai's property market continues to perform in 2025 across prices, rental yields and transaction volumes.",
            "Investors are increasingly weighing post-handover payment plans against ready stock, and the gap between the two has narrowed in several communities.",
        ],
    },
    {
        "slug": "palm-jebel-ali", "date": "2025-09-10", "title": "Palm Jebel Ali",
        "sub": "Luxury villas, waterfront living &amp; investment opportunities",
        "excerpt": "Dubai is once again reshaping its coastline with the revival of Palm Jebel Ali.",
        "img": "assets/dubai7.jpg",
        "body": [
            "Dubai is once again reshaping its coastline with the revival of Palm Jebel Ali — a development roughly twice the size of Palm Jumeirah.",
            "For buyers, the appeal is scarcity: beachfront villa plots on a master-planned frond are a finite product in Dubai.",
        ],
    },
    {
        "slug": "mercedes-benz-places-binghatti", "date": "2025-09-09",
        "title": "Mercedes-Benz Places by Binghatti", "sub": "Automotive prestige meets residential grandeur",
        "excerpt": "A branded residential tower where automotive design language carries into the architecture.",
        "img": "assets/p6.jpg",
        "body": [
            "Branded residences have become a defining feature of Dubai's luxury segment, and Mercedes-Benz Places by Binghatti is among the most distinctive entries.",
            "Branded stock typically commands a premium on entry, so the question for investors is always whether the brand sustains resale demand.",
        ],
    },
    {
        "slug": "binghatti-developers", "date": "2025-09-08", "title": "A Glimpse into Binghatti",
        "sub": "From waterfront residences to branded luxury towers",
        "excerpt": "Founded in 2008, Binghatti has become a powerhouse in Dubai's real estate landscape.",
        "img": "assets/dubai8.jpg",
        "body": [
            "Founded in 2008 by Hussain, Muhammad and Ahmed Binghatti, the developer has become a recognisable force in Dubai's skyline with a distinctive architectural signature.",
            "Their portfolio spans value-led towers through to branded luxury, which gives buyers an unusually wide entry range under one developer.",
        ],
    },
]

# ============================================================================
# FAQ
# ============================================================================
FAQS = [
    ("Can a foreigner buy property in Dubai?",
     "Yes. Non-residents and expatriates can buy freehold property in Dubai's designated freehold areas with full ownership rights. We handle the Dubai Land Department paperwork, NOC and transfer on your behalf, whether you are in the UAE or investing from abroad."),
    ("What is an off-plan payment plan?",
     "Off-plan properties are bought before completion and paid in instalments — commonly 20/80, 40/60 or with a post-handover payment plan (PHPP) that extends payments for years after you receive the keys. We model the full cash-flow for every plan before you commit."),
    ("Can I get a mortgage as a UAE resident?",
     "UAE residents can typically finance up to 75% of a property's value, subject to income eligibility. With over 40 banks and financial institutions offering mortgage products, our advisory team compares options, arranges pre-approvals and manages the process end to end."),
    ("Does buying property qualify me for a Golden Visa?",
     "Property investment at the qualifying threshold can make you eligible for a long-term UAE residency visa. Requirements change periodically, so we confirm the current criteria against your specific purchase and connect you with the right processing channel."),
    ("Can you manage my property after I buy?",
     "Yes. Our property management team currently manages over 100 projects in Dubai — covering tenant acquisition and screening, lease management, maintenance, rent collection, financial reporting and legal compliance. Reach us at pm@skyviewdubai.com."),
    ("What are the costs of buying in Dubai?",
     "Budget for the Dubai Land Department transfer fee, a trustee office registration fee, agency commission and — for mortgaged purchases — bank arrangement and valuation fees. We give you a full itemised cost sheet before you commit to anything."),
]

# ============================================================================
# ICONS
# ============================================================================
IC = {
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="10" r="3"/><path d="M12 21s-7-6-7-11a7 7 0 1114 0c0 5-7 11-7 11z"/></svg>',
    "area": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6"/></svg>',
    "bed": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M2 17v-5a2 2 0 012-2h16a2 2 0 012 2v5M2 17h20M2 18.5V21M22 18.5V21M6 10V7.5A1.5 1.5 0 017.5 6h9A1.5 1.5 0 0118 7.5V10"/></svg>',
    "bath": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 12h18v2.5a4.5 4.5 0 01-4.5 4.5h-9A4.5 4.5 0 013 14.5V12zM6 12V5.5A2 2 0 0110 5M6.5 19.5L5 22M17.5 19.5L19 22"/></svg>',
    "car": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 17h14M3 17v-5l2-5h14l2 5v5M3 17v2M21 17v2M7 13h.01M17 13h.01"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12h13M12 5l7 7-7 7"/></svg>',
    "diag": '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4v6h6M4 4l6 6"/></svg>',
    "out": '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 4h6v6M10 4L4 10"/></svg>',
    "plus": '<svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 5v8h8M5 5l8 8"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1 1 .4 1.9.7 2.8a2 2 0 01-.5 2.1L8.1 9.9a16 16 0 006 6l1.3-1.3a2 2 0 012.1-.4c.9.3 1.8.6 2.8.7a2 2 0 011.7 2z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 7l10 6 10-6"/></svg>',
    "wa": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M17.5 14.4c-.3-.2-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.7 1-.9 1.2-.2.2-.3.2-.6.1-.3-.2-1.2-.5-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6l.5-.5c.1-.2.2-.3.3-.5 0-.2 0-.4 0-.5 0-.2-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.2.2 2.1 3.2 5.1 4.5.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.7-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.2-.3-.2-.6-.4M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2m0 18.3c-1.6 0-3.2-.4-4.5-1.2l-.3-.2-3.1.8.8-3-.2-.3A8.3 8.3 0 1112 20.3"/></svg>',
    "play": '<svg viewBox="0 0 22 24" fill="currentColor"><path d="M21 12L0 24V0z"/></svg>',
}


def icon(name, size=16, cls=""):
    """Inline SVG. Always carries width/height — an SVG without intrinsic
    dimensions falls back to 300x150 and destroys the layout."""
    attrs = f'width="{size}" height="{size}" '
    if cls:
        attrs += f'class="{cls}" '
    return IC[name].replace("<svg ", "<svg " + attrs, 1)


# ============================================================================
# CHROME
# ============================================================================
NAV_ITEMS = [
    ("Listings", "listings.html"),
    ("Services", "services.html"),
    ("About Us", "about.html"),
    ("Blog", "blog.html"),
    ("Contacts", "contact.html"),
]


def rel(depth):
    return "../" * depth


def analytics(depth):
    if not CONFIG["analytics_enabled"]:
        return ("\n<!-- Analytics disabled. Set analytics_enabled = True in build.py "
                "for the production deploy only. -->\n")
    return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={CONFIG['ga4_id']}"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());gtag('config','{CONFIG['ga4_id']}');
</script>
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});
var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;
j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})
(window,document,'script','dataLayer','{CONFIG['gtm_id']}');</script>
"""


def head(title, desc, depth=0, og_img="assets/dubai5.jpg"):
    r = rel(depth)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{CONFIG['legal']}">
<link rel="icon" href="{r}assets/logo.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{r}{og_img}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&family=Host+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}styles.css">
{analytics(depth)}</head>
<body{' data-form-endpoint="' + CONFIG['form_endpoint'] + '"' if CONFIG['form_endpoint'] else ''} data-wa="{CONFIG['whatsapp']}">
"""


def nav(active="", depth=0, solid=False):
    r = rel(depth)
    cur = ' aria-current="page"'
    links = "".join(
        '<a href="{}{}"{}>{}</a>'.format(r, href, cur if label == active else "", label)
        for label, href in NAV_ITEMS)
    return f"""
<a class="skip" href="#main">Skip to content</a>
<header class="nav{' nav--solid' if solid else ''}">
  <div class="shell nav__in">
    <a class="nav__brand" href="{r}index.html">
      <span>SKY VIEW</span>
      <small>REAL ESTATE</small>
    </a>
    <nav class="nav__links" aria-label="Main">{links}</nav>
    <div class="nav__cta">
      <a class="btn btn--light" href="{r}contact.html">Work with us</a>
      <button class="nav__burger" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<main id="main">
"""


def footer(depth=0):
    r = rel(depth)
    socials = "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>'
                      for n, u in CONFIG["social"].items())
    svc = "".join(f'<li><a href="{r}services.html#{s["slug"]}">{s["title"]}</a></li>' for s in SERVICES)
    return f"""</main>

<section class="pre-footer">
  <h2 class="reveal">Let's find<br><em class="serif">your perfect</em><br>home</h2>
</section>

<footer class="footer">
  <div class="shell">
    <div class="footer__grid">
      <div>
        <h5>Properties</h5>
        <ul>
          <li><a href="{r}listings.html?purpose=sale">Buy in Dubai</a></li>
          <li><a href="{r}listings.html?purpose=rent">Rent in Dubai</a></li>
          <li><a href="{r}listings.html">All listings</a></li>
          <li><a href="{r}contact.html">List your property</a></li>
        </ul>
      </div>
      <div>
        <h5>Services</h5>
        <ul>{svc}</ul>
      </div>
      <div>
        <h5>Company</h5>
        <ul>
          <li><a href="{r}about.html">About us</a></li>
          <li><a href="{r}team.html">Our team</a></li>
          <li><a href="{r}careers.html">Careers</a></li>
          <li><a href="{r}blog.html">Blog</a></li>
          <li><a href="{r}contact.html">Contact</a></li>
        </ul>
      </div>
      <div>
        <h5>Offices</h5>
        <address>
          {CONFIG['hq']}<br><br>
          {CONFIG['branch']}<br><br>
          {CONFIG['hours']}
        </address>
      </div>
      <div>
        <h5>Get listing updates</h5>
        <form class="footer__news" id="newsForm">
          <input type="email" name="email" placeholder="you@email.com" aria-label="Email address" required>
          <button type="submit" aria-label="Subscribe">{icon('arrow', 18)}</button>
        </form>
        <div class="footer__contact">
          <div><small>Phone</small><a href="tel:{CONFIG['phone_landline'].replace(' ', '')}">{CONFIG['phone_landline']}</a></div>
          <div><small>Email</small><a href="mailto:{CONFIG['email']}">{CONFIG['email']}</a></div>
        </div>
      </div>
    </div>

    <div class="footer__bottom">
      <span class="footer__brand">SKY VIEW</span>
      <span>© 2026 {CONFIG['legal']}. RERA registered. <a href="{r}privacy.html">Privacy</a> · <a href="{r}terms.html">Terms</a></span>
      <div class="socials">{socials}</div>
    </div>
  </div>
</footer>

<a class="wa" href="{WA_BASE}" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp">{icon('wa', 27)}</a>

<script src="{r}script.js"></script>
</body>
</html>
"""


# ============================================================================
# COMPONENTS
# ============================================================================
def listing_card(l, depth=0, reveal=True):
    r = rel(depth)
    note = (f' <small>{l["price_note"]}</small>' if l["price_note"] else "")
    return f"""
      <article class="card{' reveal' if reveal else ''}" data-type="{l['purpose'].lower()}" data-kind="{l['type'].lower()}">
        <a class="card__link" href="{r}property/{l['slug']}.html">
          <div class="card__media">
            <img src="{r}{l['img']}" alt="{l['type']} in {l['location']}" loading="lazy">
            <div class="card__tags"><span class="tag tag--cream">{l['type']}</span><span class="tag">{l['purpose']}</span></div>
          </div>
          <div class="card__body">
            <h3>{l['title']}</h3>
            <p class="card__loc">{icon('pin', 13)}{l['location']}</p>
          </div>
          <div class="card__foot">
            <div class="specs">
              <span>{icon('area', 14)}{l['area']} sq.ft</span>
              <span>{icon('bed', 14)}{l['beds']}</span>
              <span>{icon('bath', 14)}{l['baths']}</span>
            </div>
            <div class="price">{l['price']}{note}</div>
          </div>
        </a>
      </article>"""


def page_hero(eyebrow, title, sub="", img="assets/dubai2.jpg", depth=0):
    r = rel(depth)
    return f"""
<section class="phero">
  <div class="phero__bg"><img src="{r}{img}" alt=""></div>
  <div class="shell">
    <p class="phero__eyebrow">{eyebrow}</p>
    <h1 class="phero__title">{title}</h1>
    {f'<p class="phero__sub">{sub}</p>' if sub else ''}
  </div>
</section>"""


def contact_block(depth=0, heading="Discover<br><em class=\"serif\">your ideal</em><br>place"):
    r = rel(depth)
    return f"""
<section class="contact" id="contact">
  <div class="contact__bg"><img src="{r}assets/dubai1.jpg" alt="" loading="lazy"></div>
  <div class="shell">
    <p class="contact__eyebrow">Message</p>
    <div class="contact__box reveal">
      <div class="contact__left">
        <h2>{heading}</h2>
        <p>Tell us what you're looking for, and we'll guide you to the best options across Dubai.</p>
        <div class="contact__meta">
          <a href="tel:{CONFIG['phone_landline'].replace(' ', '')}">{icon('phone', 15)}{CONFIG['phone_landline']}</a>
          <a href="mailto:{CONFIG['email']}">{icon('mail', 15)}{CONFIG['email']}</a>
          <a href="https://maps.google.com/?q=Clover+Bay+Tower+Business+Bay+Dubai" target="_blank" rel="noopener">{icon('pin', 15)}Clover Bay Tower, Business Bay</a>
        </div>
      </div>

      <form class="contact__form" id="leadForm" novalidate>
        <div class="field">
          <label for="f-name">Name</label>
          <input id="f-name" name="name" type="text" placeholder="Your full name" required autocomplete="name">
        </div>
        <div class="field">
          <label for="f-email">Email</label>
          <input id="f-email" name="email" type="email" placeholder="you@email.com" required autocomplete="email">
        </div>
        <div class="field">
          <label for="f-phone">Phone</label>
          <input id="f-phone" name="phone" type="tel" placeholder="+971 50 000 0000" autocomplete="tel">
        </div>
        <div class="field">
          <label for="f-msg">Message</label>
          <textarea id="f-msg" name="message" placeholder="Tell us what you're looking for"></textarea>
        </div>
        <button class="btn" type="submit">Submit</button>
        <p class="form-note" id="formNote" role="status" aria-live="polite" hidden></p>
      </form>
    </div>
  </div>
</section>"""


def faq_block(limit=None):
    items = FAQS[:limit] if limit else FAQS
    out = []
    for i, (q, a) in enumerate(items):
        out.append(f"""      <details class="faq-item"{' open' if i == 0 else ''}>
        <summary class="faq-q">{q}{icon('plus', 18)}</summary>
        <div class="faq-a">{a}</div>
      </details>""")
    return "\n".join(out)


# ============================================================================
# PAGES
# ============================================================================
def build_home():
    cards = "".join(listing_card(l) for l in LISTINGS)
    comms = "".join(f"""
      <a class="loc reveal" href="listings.html">
        <div class="loc__img"><img src="{img}" alt="{n}" loading="lazy"></div>
        <div class="loc__b"><h3>{icon('pin', 14)}{n}</h3><p>{d}</p></div>
      </a>""" for n, d, img in COMMUNITIES)

    experts = "".join(f"""
      <article class="member reveal">
        <div class="member__img"><img src="{img}" alt="{n}" loading="lazy"></div>
        <h3>{n}</h3><p>{role}</p>
      </article>""" for n, role, img in LEADERSHIP[1:5])

    vid = CONFIG["showreel_video"]

    html = head(f"{CONFIG['name']} — Your Dream Home in Dubai Awaits",
                f"{CONFIG['legal']} — top-rated investment advisory and brokerage in Dubai since {CONFIG['founded']}. Buy, rent and invest in Dubai property.")
    html += nav("", 0)
    html += f"""
<section class="hero" id="top">
  <div class="hero__bg"><img src="assets/dubai5.jpg" alt="Downtown Dubai skyline at sunset" fetchpriority="high"></div>
  <div class="hero__top">
    <span>We help you find<br>the right home in Dubai</span>
    <span>since {CONFIG['founded']}</span>
  </div>
  <h1>Start Your <em>Dubai</em> Home Discovery</h1>
  <div class="hero__foot">
    <a class="btn btn--light" href="listings.html">View All Listings</a>
    <a class="hero__chip" href="property/{LISTINGS[0]['slug']}.html">
      <img src="{LISTINGS[0]['img']}" alt="{LISTINGS[0]['location']}">
      <div class="t">{LISTINGS[0]['type']}</div>
      <div class="s">{LISTINGS[0]['area']} sq.ft</div>
      <div class="r"><span>DAMAC Islands</span>{icon('out', 14)}</div>
    </a>
  </div>
</section>

<section class="sec" id="listings">
  <div class="shell">
    <div class="sec__head reveal">
      <p class="eyebrow">Properties</p>
      <h2>Featured Dubai listings</h2>
      <div class="filters" role="tablist" aria-label="Filter listings">
        <button role="tab" aria-selected="true" data-filter="all">All</button>
        <button role="tab" aria-selected="false" data-filter="sale">Sale</button>
        <button role="tab" aria-selected="false" data-filter="rent">Rent</button>
      </div>
    </div>
    <div class="grid-cards" id="cardGrid">{cards}
    </div>
    <div class="sec__foot reveal"><a class="btn" href="listings.html">View All Properties</a></div>
  </div>
</section>

<section class="sec" id="about">
  <div class="shell">
    <div class="discover reveal">
      <p class="eyebrow">About Us</p>
      <h2>Discover</h2>
    </div>
    <div class="about-grid">
      <div class="about-stack">
        <article class="dcard reveal">
          <div class="dcard__img"><img src="assets/p2.jpg" alt="" loading="lazy"></div>
          <div class="dcard__row"><h3>Local expertise</h3><span>01</span></div>
          <p>Twenty years inside Dubai's communities — we know the pricing trends, service charges and hidden trade-offs.</p>
        </article>
        <article class="dcard reveal">
          <div class="dcard__img"><img src="assets/p6.jpg" alt="" loading="lazy"></div>
          <div class="dcard__row"><h3>Clear process</h3><span>02</span></div>
          <p>From first viewing to DLD transfer and handover, every step is explained before you commit.</p>
        </article>
        <article class="dcard reveal">
          <div class="dcard__img"><img src="assets/p5.jpg" alt="" loading="lazy"></div>
          <div class="dcard__row"><h3>Tailored support</h3><span>03</span></div>
          <p>RERA-registered advisors matching your goals, budget and payment plan — resale or off-plan.</p>
        </article>
      </div>
      <div class="about-media reveal"><img src="assets/dubai8.jpg" alt="New residential towers in Dubai" loading="lazy"></div>
      <div class="about-copy reveal">
        <p class="eyebrow">A trusted name in Dubai real estate</p>
        <h3>We make Dubai property feel clear</h3>
        <p>{CONFIG['legal']}, established in {CONFIG['founded']}, is a top-rated investment advisory and brokerage house in Dubai — serving local and offshore clients across the city's most dynamic communities. We simplify the process so you can focus on the move ahead.</p>
        <div class="stories">
          <div class="avatars">
            <img src="assets/team-akash.jpg" alt="">
            <img src="assets/team-rahul.jpg" alt="">
            <img src="assets/team-kadir.jpg" alt="">
          </div>
          <a class="arrow-btn" href="about.html" aria-label="Read more about us">{icon('arrow', 17)}</a>
          <small>Read Our<br>Company Story</small>
        </div>
      </div>
    </div>

    <div class="stats">
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="6">6</span>B+</div>
        <h4>AED in Property Sold</h4>
        <p>Two decades of completed transactions across Dubai.</p>
      </div>
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="100">100</span>+</div>
        <h4>Projects Managed</h4>
        <p>Bespoke property management tailored to each portfolio.</p>
      </div>
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="68">68</span></div>
        <h4>Specialist Advisors</h4>
        <p>RERA-registered consultants across sales, leasing and investment.</p>
      </div>
    </div>
  </div>
</section>

<section class="sec--tight">
  <div class="shell">
    <nav class="cats reveal" aria-label="Property types">
      <a href="listings.html?kind=apartment">{icon('diag', 14)}Apartment</a>
      <a href="listings.html?kind=villa">{icon('diag', 14)}Villa</a>
      <a href="listings.html?kind=townhouse">{icon('diag', 14)}Townhouse</a>
      <a href="listings.html?kind=penthouse">{icon('diag', 14)}Penthouse</a>
      <a href="listings.html">{icon('diag', 14)}All listings</a>
    </nav>
  </div>
</section>

<section class="sec showreel">
  <div class="shell">
    <p class="eyebrow reveal">Showreel</p>
    <h2 class="reveal">Dubai property choice<br><em class="serif">should feel</em> inspiring</h2>
    <div class="reel reveal" id="reel" data-video="{vid}" data-title="{CONFIG['showreel_title']}">
      <img src="https://i.ytimg.com/vi/{vid}/maxresdefault.jpg" alt="{CONFIG['showreel_title']}" loading="lazy"
           onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/{vid}/hqdefault.jpg'">
      <button class="reel__play" aria-label="Play showreel video">{icon('play', 22)}</button>
    </div>
  </div>
</section>

<section class="sec" id="locations">
  <div class="shell">
    <div class="loc-head reveal">
      <div><p class="eyebrow">Location</p><h2>Explore the right community</h2></div>
      <p>Explore Dubai neighbourhoods by lifestyle, commute, price range and atmosphere.</p>
    </div>
    <div class="loc-grid">{comms}
    </div>
  </div>
</section>

<section class="sec reviews" id="reviews" data-reviews>
  <div class="shell">
    <div class="sec__head reveal">
      <p class="eyebrow">Reviews</p>
      <h2>Client stories that inspire</h2>
    </div>
    <div class="rev-track" id="revTrack"></div>
    <div class="dots" id="revDots"></div>
  </div>
</section>

<section class="sec team" id="team">
  <div class="team__ghost" aria-hidden="true">Experts</div>
  <div class="shell">
    <div class="team__head reveal"><p class="eyebrow">Team</p><h2>Meet Our Experts</h2></div>
    <div class="team-grid">
      <article class="member reveal">
        <div class="member__img"><img src="{LEADERSHIP[1][2]}" alt="{LEADERSHIP[1][0]}" loading="lazy"></div>
        <h3>{LEADERSHIP[1][0]}</h3><p>{LEADERSHIP[1][1]}</p>
      </article>
      <p class="member__note reveal">Our experts know the Dubai market and help you make the right choice.</p>{experts}
    </div>
    <div class="sec__foot reveal"><a class="btn" href="team.html">Meet the full team</a></div>
  </div>
</section>

<section class="sec" id="faq">
  <div class="shell faq-grid">
    <div class="faq-left reveal">
      <p class="eyebrow">Your questions</p>
      <h2>Frequently<br>Asked<br>Questions</h2>
      <div class="faq-help">
        <div class="avatars">
          <img src="assets/team-pratik.jpg" alt="">
          <img src="assets/team-bana.jpg" alt="">
          <img src="assets/team-kadir.jpg" alt="">
        </div>
        <a class="arrow-btn" href="contact.html" aria-label="Contact our team">{icon('arrow', 17)}</a>
        <small>Our team is<br>here to help</small>
      </div>
    </div>
    <div class="faq-list reveal">
{faq_block(5)}
    </div>
  </div>
</section>
{contact_block()}
"""
    html += footer()
    write("index.html", html)


def build_listings():
    cards = "".join(listing_card(l) for l in LISTINGS)
    html = head(f"Properties for Sale &amp; Rent in Dubai — {CONFIG['name']}",
                "Browse apartments, villas, townhouses and penthouses for sale and rent across Dubai.")
    html += nav("Listings", 0, solid=True)
    html += page_hero("Properties", "Dubai listings",
                      "Apartments, villas, townhouses and penthouses across Dubai's most active communities.",
                      "assets/dubai2.jpg")
    html += f"""
<section class="sec">
  <div class="shell">
    <form class="searchbar reveal" id="searchBar" role="search" aria-label="Search properties">
      <div class="sb-field">
        <label for="s-purpose">Purpose</label>
        <select id="s-purpose" name="purpose"><option value="">Any</option><option value="sale">Buy</option><option value="rent">Rent</option></select>
      </div>
      <div class="sb-field">
        <label for="s-kind">Property type</label>
        <select id="s-kind" name="kind"><option value="">Any</option>
          <option value="apartment">Apartment</option><option value="villa">Villa</option>
          <option value="townhouse">Townhouse</option><option value="penthouse">Penthouse</option></select>
      </div>
      <div class="sb-field">
        <label for="s-beds">Beds</label>
        <select id="s-beds" name="beds"><option value="">Any</option><option>1</option><option>2</option><option>3</option><option>4</option><option value="5">5+</option></select>
      </div>
      <div class="sb-field">
        <label for="s-q">Keyword</label>
        <input id="s-q" name="q" type="search" placeholder="Community, project or feature">
      </div>
      <button class="btn" type="submit">Search</button>
    </form>

    <div class="list-meta">
      <p id="resultCount" role="status" aria-live="polite">{len(LISTINGS)} properties</p>
      <div class="sb-field sb-field--inline">
        <label for="s-sort">Sort</label>
        <select id="s-sort"><option value="new">Newest</option><option value="low">Price: lowest first</option><option value="high">Price: highest first</option><option value="area">Largest first</option></select>
      </div>
    </div>

    <div class="grid-cards" id="cardGrid">{cards}
    </div>
    <p class="empty-state" id="emptyState" hidden>No properties match those filters. <button type="button" class="linklike" id="clearFilters">Clear all filters</button></p>
  </div>
</section>
{contact_block(heading='Looking for<br><em class="serif">something</em><br>specific?')}
"""
    html += footer()
    write("listings.html", html)


def build_property_pages():
    os.makedirs(os.path.join(OUT, "property"), exist_ok=True)
    for l in LISTINGS:
        others = [x for x in LISTINGS if x["slug"] != l["slug"]][:3]
        sim = "".join(listing_card(x, depth=1) for x in others)
        desc = "".join(f"<p>{p}</p>" for p in l["desc"])
        details = "".join(f"<li>{d}</li>" for d in l["details"])
        amen = "".join(f"<li>{a}</li>" for a in l["amenities"])
        wa = (f"https://wa.me/{l['agent_phone']}?text=I'm%20interested%20in%20your%20listing%3A%20"
              + l["title"].replace(" ", "%20").replace("|", "%7C"))
        note = f' <small>{l["price_note"]}</small>' if l["price_note"] else ""

        html = head(f"{l['title']} — {l['location']} | {CONFIG['name']}",
                    f"{l['type']} for {l['purpose'].lower()} in {l['location']}. {l['beds']} bed, {l['baths']} bath, {l['area']} sq.ft. {l['price']}.",
                    depth=1, og_img=l["img"])
        html += nav("Listings", 1, solid=True)
        html += f"""
<div class="shell">
  <nav class="crumbs" aria-label="Breadcrumb">
    <a href="../index.html">Home</a> › <a href="../listings.html">Listings</a> › <span>{l['type']}</span>
  </nav>

  <section class="pdp">
    <div class="pdp__media">
      <img src="../{l['img']}" alt="{l['title']}" fetchpriority="high">
      <div class="card__tags"><span class="tag tag--cream">{l['type']}</span><span class="tag">{l['purpose']}</span></div>
    </div>

    <div class="pdp__grid">
      <div class="pdp__main">
        <h1>{l['title']}</h1>
        <p class="pdp__loc">{icon('pin', 15)}{l['area_full']}</p>

        <div class="pdp__specs">
          <div><span class="k">{icon('bed', 15)}Bedrooms</span><span class="v">{l['beds']}</span></div>
          <div><span class="k">{icon('bath', 15)}Bathrooms</span><span class="v">{l['baths']}</span></div>
          <div><span class="k">{icon('car', 15)}Parking</span><span class="v">{l['parking']}</span></div>
          <div><span class="k">{icon('area', 15)}Area</span><span class="v">{l['area']} sq.ft</span></div>
        </div>

        <div class="prose">{desc}</div>

        <h2 class="pdp__h">Property details</h2>
        <ul class="ticks">{details}</ul>

        <h2 class="pdp__h">Amenities &amp; facilities</h2>
        <ul class="ticks ticks--2">{amen}</ul>
      </div>

      <aside class="pdp__side">
        <div class="pdp__price">
          <small>{'Price' if l['purpose'] == 'Sale' else 'Annual rent'}</small>
          <strong>{l['price']}{note}</strong>
          <span class="ref">Ref. {l['ref']}</span>
        </div>
        <div class="pdp__agent">
          <img src="../{l['agent_img']}" alt="{l['agent']}">
          <div>
            <strong>{l['agent']}</strong>
            <small>Property Consultant</small>
          </div>
        </div>
        <a class="btn btn--wa" href="{wa}" target="_blank" rel="noopener">{icon('wa', 17)}WhatsApp enquiry</a>
        <a class="btn" href="tel:{CONFIG['phone_landline'].replace(' ', '')}">{icon('phone', 17)}Call us</a>
        <a class="btn btn--outline" href="../contact.html">{icon('mail', 17)}Request a viewing</a>
        <p class="pdp__legal">{CONFIG['legal']} · RERA registered<br>{CONFIG['hq']}</p>
      </aside>
    </div>
  </section>
</div>

<section class="sec">
  <div class="shell">
    <div class="sec__head reveal"><p class="eyebrow">More options</p><h2>Similar properties</h2></div>
    <div class="grid-cards">{sim}
    </div>
  </div>
</section>
"""
        html += footer(depth=1)
        write(f"property/{l['slug']}.html", html)


def build_services():
    blocks = []
    for i, s in enumerate(SERVICES):
        body = "".join(f"<p>{p}</p>" for p in s["body"])
        hi = "".join(f"<li>{h}</li>" for h in s["highlights"])
        inc = "".join(f"<li>{x}</li>" for x in s["includes"])
        blocks.append(f"""
  <section class="svc{' svc--alt' if i % 2 else ''}" id="{s['slug']}">
    <div class="shell svc__in">
      <div class="svc__media reveal"><img src="{s['img']}" alt="{s['title']}" loading="lazy"></div>
      <div class="svc__body reveal">
        <p class="eyebrow">0{i + 1} — Service</p>
        <h2>{s['title']}</h2>
        <p class="svc__lede">{s['lede']}</p>
        <div class="prose">{body}</div>
        <ul class="ticks">{hi}</ul>
        <h3 class="svc__h">What's included</h3>
        <ul class="chips">{inc}</ul>
      </div>
    </div>
  </section>""")

    html = head(f"Services — {CONFIG['name']}",
                "Property management, investment consultancy, developer consultancy and mortgage advisory in Dubai.")
    html += nav("Services", 0, solid=True)
    html += page_hero("What we do", "Services",
                      "We create sustainable economic value for clients, investors and co-partners through assets that provide high returns and significant upside potential.",
                      "assets/dubai8.jpg")
    html += "".join(blocks)
    html += contact_block(heading='Talk to<br><em class="serif">an advisor</em>')
    html += footer()
    write("services.html", html)


def build_about():
    html = head(f"About — {CONFIG['name']}",
                f"{CONFIG['legal']}, established {CONFIG['founded']} — a top-rated investment advisory and brokerage house in Dubai.")
    html += nav("About Us", 0, solid=True)
    html += page_hero("Our company", "Elevating dreams,<br>redefining excellence",
                      f"Dubai's premium real estate since {CONFIG['founded']}. Over AED 6 billion worth of property sold.",
                      "assets/about.jpg")
    html += f"""
<section class="sec">
  <div class="shell about-page">
    <div class="prose prose--lead reveal">
      <p>{CONFIG['legal']}, established in the year {CONFIG['founded']}, is a top-rated investment advisory and brokerage house in Dubai providing services for local and offshore clients to invest in the ever-growing and dynamic Dubai real estate market.</p>
      <p>The mission of the company is to create sustainable economic value for its clients, investors and co-partners through the acquisition of assets that provide high returns and display significant upside potential.</p>
      <p>Sky View offers personalised sessions with clients — both individuals and institutional investors worldwide — understands their needs and advises them on various profitable options in terms of property investments in the Dubai market.</p>
      <p>The young, dynamic and well-experienced management team, along with highly motivated sales professionals, manages portfolios efficiently, which has helped in deriving a large client base and the confidence of investors.</p>
      <p>Well-known builders and developers of Dubai such as Emaar and DAMAC Properties have placed considerable confidence in {CONFIG['legal']} because of our in-depth knowledge of the property market, investor management and responsiveness.</p>
      <p>A unique feature of our service is that every client associated with us is notified and updated with current market trends, which enables them to assess the marketability of their properties.</p>
      <p>{CONFIG['legal']} are independent real estate agents registered with the Real Estate Regulatory Authority (RERA) and the Dubai Economic Department, and hold a certificate to conduct sales and brokerage in the UAE.</p>
    </div>

    <div class="stats">
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="6">6</span>B+</div>
        <h4>AED in Property Sold</h4><p>Two decades of completed transactions.</p>
      </div>
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="20">20</span></div>
        <h4>Years in the Market</h4><p>Serving Dubai since {CONFIG['founded']}.</p>
      </div>
      <div class="stat reveal">
        <div class="stat__n"><span class="count" data-to="68">68</span></div>
        <h4>Specialist Advisors</h4><p>Across sales, leasing and investment.</p>
      </div>
    </div>
  </div>
</section>

<section class="sec ceo">
  <div class="shell ceo__in">
    <div class="ceo__img reveal"><img src="assets/team-akash.jpg" alt="Akash Kanjwani, Chief Executive Officer" loading="lazy"></div>
    <div class="ceo__body reveal">
      <p class="eyebrow">CEO's message</p>
      <blockquote>“As we celebrate 20 years of serving this dynamic market, I'm reminded of the countless stories of clients whose lives we've touched. It's more than just property — it's about trust, long-lasting relationships, and being a part of our clients' success stories.”</blockquote>
      <div class="prose">
        <p>At Sky View Real Estate, our journey began with a clear vision: to offer the finest investment advice and real estate consultancy in Dubai. What drives us every day is our commitment to helping people realise their dreams, whether that's finding the perfect home or making sound investment choices.</p>
        <p>I believe that every property transaction is more than just a financial decision; it's about understanding the aspirations and emotions tied to homeownership. Our team embodies professionalism, integrity and a deep commitment to serving you with the highest level of expertise.</p>
      </div>
      <p class="ceo__sign">— Akash Kanjwani, Chief Executive Officer</p>
    </div>
  </div>
</section>

<section class="sec">
  <div class="shell">
    <div class="sec__head reveal"><p class="eyebrow">Recognition</p><h2>Credentials that hold up</h2></div>
    <div class="trust-grid">
      <div class="trust reveal"><h3>RERA &amp; DED registered</h3><p>Licensed to conduct sales and brokerage in the UAE.</p></div>
      <div class="trust reveal"><h3>Great Place to Work certified</h3><p>Independently certified on workplace culture.</p></div>
      <div class="trust reveal"><h3>Developer partnerships</h3><p>Emaar, DAMAC, Sobha, Aldar, Danube, Binghatti, MAG and more.</p></div>
      <div class="trust reveal"><h3>Two offices in Dubai</h3><p>Business Bay headquarters and an Al Barsha sales centre.</p></div>
    </div>
  </div>
</section>
{contact_block()}
"""
    html += footer()
    write("about.html", html)


def build_team():
    lead = "".join(f"""
      <article class="member reveal">
        <div class="member__img"><img src="{img}" alt="{n}" loading="lazy"></div>
        <h3>{n}</h3><p>{role}</p>
      </article>""" for n, role, img in LEADERSHIP)

    groups = "".join(f"""
      <div class="roster__group reveal">
        <h3>{title}</h3>
        <ul>{''.join(f'<li>{p}</li>' for p in people)}</ul>
      </div>""" for title, people in ROSTER)

    total = len(LEADERSHIP) + sum(len(p) for _, p in ROSTER)

    html = head(f"Our Team — {CONFIG['name']}",
                f"Meet the {total}-strong team at {CONFIG['legal']} — RERA-registered advisors across sales, leasing, investment and property management.")
    html += nav("About Us", 0, solid=True)
    html += page_hero("Team", "Meet our experts",
                      f"{total} specialists across sales, leasing, investment advisory and property management.",
                      "assets/hero-banner1.jpg")
    html += f"""
<section class="sec">
  <div class="shell">
    <div class="sec__head reveal"><p class="eyebrow">Leadership</p><h2>The people who set the standard</h2></div>
    <div class="team-grid team-grid--flat">{lead}
    </div>
  </div>
</section>

<section class="sec sec--tight">
  <div class="shell">
    <div class="sec__head reveal"><p class="eyebrow">Full roster</p><h2>The wider team</h2></div>
    <div class="roster">{groups}
    </div>
  </div>
</section>
{contact_block(heading='Work with<br><em class="serif">our team</em>')}
"""
    html += footer()
    write("team.html", html)


def build_blog():
    os.makedirs(os.path.join(OUT, "blog"), exist_ok=True)
    cards = "".join(f"""
      <article class="post reveal">
        <a href="blog/{p['slug']}.html">
          <div class="post__img"><img src="{p['img']}" alt="{p['title']}" loading="lazy"></div>
          <div class="post__b">
            <time datetime="{p['date']}">{p['date']}</time>
            <h3>{p['title']}</h3>
            <p>{p['excerpt']}</p>
            <span class="readmore">Read more {icon('arrow', 15)}</span>
          </div>
        </a>
      </article>""" for p in POSTS)

    html = head(f"Blog — {CONFIG['name']}",
                "Dubai real estate market insight, project launches and investor guidance from Sky View Real Estate.")
    html += nav("Blog", 0, solid=True)
    html += page_hero("Insight", "Blog", "Market updates, project launches and investor guidance.",
                      "assets/dubai3.jpg")
    html += f"""
<section class="sec">
  <div class="shell"><div class="post-grid">{cards}
  </div></div>
</section>
"""
    html += footer()
    write("blog.html", html)

    for i, p in enumerate(POSTS):
        nxt = POSTS[(i + 1) % len(POSTS)]
        body = "".join(f"<p>{x}</p>" for x in p["body"])
        html = head(f"{p['title']} — {CONFIG['name']}", p["excerpt"], depth=1, og_img=p["img"])
        html += nav("Blog", 1, solid=True)
        html += f"""
<article class="shell post-page">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> › <a href="../blog.html">Blog</a> › <span>{p['title']}</span></nav>
  <header class="post-page__head">
    <time datetime="{p['date']}">{p['date']}</time>
    <h1>{p['title']}</h1>
    <p class="post-page__sub">{p['sub']}</p>
  </header>
  <div class="post-page__img"><img src="../{p['img']}" alt="{p['title']}" fetchpriority="high"></div>
  <div class="prose prose--lead">{body}</div>
  <div class="post-page__foot">
    <a class="btn" href="../listings.html">Browse listings</a>
    <a class="btn btn--outline" href="../blog/{nxt['slug']}.html">Next: {nxt['title']} {icon('arrow', 16)}</a>
  </div>
</article>
"""
        html += footer(depth=1)
        write(f"blog/{p['slug']}.html", html)


def build_contact():
    html = head(f"Contact — {CONFIG['name']}",
                f"Get in touch with {CONFIG['legal']}. Two Dubai offices, phone, email and WhatsApp.")
    html += nav("Contacts", 0, solid=True)
    html += page_hero("Contact", "Let's talk", "We'd love to hear from you — by phone, email or the form below.",
                      "assets/dubai7.jpg")
    html += f"""
<section class="sec">
  <div class="shell">
    <div class="office-grid">
      <div class="office reveal">
        <h3>Headquarters</h3>
        <address>{CONFIG['hq']}</address>
        <a href="https://maps.google.com/?q=Clover+Bay+Tower+Business+Bay+Dubai" target="_blank" rel="noopener">Open in Maps {icon('out', 13)}</a>
      </div>
      <div class="office reveal">
        <h3>Sales Centre</h3>
        <address>{CONFIG['branch']}</address>
        <a href="https://maps.google.com/?q=Hessa+Street+Al+Barsha+Third+Dubai" target="_blank" rel="noopener">Open in Maps {icon('out', 13)}</a>
      </div>
      <div class="office reveal">
        <h3>Talk to us</h3>
        <ul class="contact-list">
          <li>{icon('phone', 15)}<a href="tel:{CONFIG['phone_landline'].replace(' ', '')}">{CONFIG['phone_landline']}</a></li>
          <li>{icon('phone', 15)}<a href="tel:{CONFIG['phone_mobile'].replace(' ', '')}">{CONFIG['phone_mobile']}</a></li>
          <li>{icon('mail', 15)}<a href="mailto:{CONFIG['email']}">{CONFIG['email']}</a></li>
          <li>{icon('mail', 15)}<a href="mailto:{CONFIG['email_pm']}">{CONFIG['email_pm']} (property management)</a></li>
          <li>{icon('mail', 15)}<a href="mailto:{CONFIG['email_hr']}">{CONFIG['email_hr']} (careers)</a></li>
        </ul>
        <p class="muted">{CONFIG['hours']}</p>
      </div>
    </div>
  </div>
</section>
{contact_block()}
<section class="sec sec--tight">
  <div class="shell faq-grid">
    <div class="faq-left reveal"><p class="eyebrow">Your questions</p><h2>Frequently<br>Asked<br>Questions</h2></div>
    <div class="faq-list reveal">
{faq_block()}
    </div>
  </div>
</section>
"""
    html += footer()
    write("contact.html", html)


def build_careers():
    vacancies = ["Real Estate Sales Director", "Receptionist (UAE Nationals only)",
                 "Leasing Consultant (Females Only)", "Social Media Content Creator — Real Estate",
                 "Property Administrator / Listing Management"]
    vac = "".join(f"""
      <li class="vacancy reveal">
        <div><h3>{v}</h3><p>Dubai · Full time</p></div>
        <a class="btn btn--outline" href="mailto:{CONFIG['email_hr']}?subject=Application%3A%20{v.replace(' ', '%20')}">Apply</a>
      </li>""" for v in vacancies)

    html = head(f"Careers — {CONFIG['name']}",
                f"Join {CONFIG['legal']} — a Great Place to Work certified brokerage in Dubai.")
    html += nav("About Us", 0, solid=True)
    html += page_hero("Careers", "Grow with us",
                      "Great Place to Work certified. We believe the fastest way to grow our organisation is by growing our people.",
                      "assets/hero-banner1.jpg")
    html += f"""
<section class="sec">
  <div class="shell about-page">
    <div class="prose prose--lead reveal">
      <p>As the leading brokerage and investment advisory company in Dubai, we firmly believe that the fastest way to grow our organisation is by growing our people. We take pride in being a culturally diverse workplace where all genders are equal.</p>
      <p>We are proud to be <strong>Great Place to Work Certified</strong> — a testament to our commitment to creating a supportive, inclusive and dynamic work environment.</p>
      <p>By joining Sky View you'll be part of an energetic workspace with industry-experienced, well-trained staff who will guide and support you. Our monthly team-building activities and continuous knowledge-sharing about the latest market trends ensure you're always growing professionally.</p>
      <p>We believe in empowering our team through innovative tools, including our in-house real estate training platform, dedicated trainers and ongoing leadership support — plus competitive earning potential and incentives.</p>
    </div>
  </div>
</section>

<section class="sec sec--tight">
  <div class="shell">
    <div class="sec__head reveal"><p class="eyebrow">Open roles</p><h2>Current vacancies</h2></div>
    <ul class="vacancies">{vac}
    </ul>
    <p class="center muted">Don't see your role? Send your CV to <a href="mailto:{CONFIG['email_hr']}">{CONFIG['email_hr']}</a>.</p>
  </div>
</section>
{contact_block(heading='Start<br><em class="serif">your career</em>')}
"""
    html += footer()
    write("careers.html", html)


def build_simple_pages():
    # Thank you
    html = head(f"Thank you — {CONFIG['name']}", "We've received your enquiry.")
    html += nav("", 0, solid=True)
    html += f"""
<section class="sec center-page">
  <div class="shell">
    <p class="eyebrow">Message sent</p>
    <h1 class="display big">Thank you</h1>
    <p class="lede center-p">We've received your enquiry and an advisor will be in touch shortly. For anything urgent, reach us on {CONFIG['phone_landline']} or by WhatsApp.</p>
    <div class="center-actions">
      <a class="btn" href="listings.html">Browse listings</a>
      <a class="btn btn--outline" href="index.html">Back home</a>
    </div>
  </div>
</section>
"""
    html += footer()
    write("thank-you.html", html)

    # 404
    html = head(f"Page not found — {CONFIG['name']}", "That page doesn't exist.")
    html += nav("", 0, solid=True)
    html += """
<section class="sec center-page">
  <div class="shell">
    <p class="eyebrow">Error 404</p>
    <h1 class="display big">Page not found</h1>
    <p class="lede center-p">The page you're looking for has moved or no longer exists.</p>
    <div class="center-actions">
      <a class="btn" href="/listings.html">Browse listings</a>
      <a class="btn btn--outline" href="/index.html">Back home</a>
    </div>
  </div>
</section>
"""
    html += footer()
    write("404.html", html)

    # Privacy + Terms
    legal_pages = [
        ("privacy.html", "Privacy Policy", [
            ("What we collect", "When you submit an enquiry form, subscribe to listing updates or contact us by phone, email or WhatsApp, we collect the details you provide — typically your name, email address, phone number and what you're looking for."),
            ("How we use it", "We use your details solely to respond to your enquiry, match you with suitable properties and — if you opt in — send listing updates. We do not sell your personal data."),
            ("Sharing", "We may share your details with the specific advisor handling your enquiry and, where a transaction proceeds, with the relevant developer, bank or the Dubai Land Department as required to complete it."),
            ("Retention", "We retain enquiry records for as long as needed to serve you and to meet UAE regulatory and RERA record-keeping obligations."),
            ("Your rights", "You can request access to, correction of, or deletion of your personal data at any time by emailing " + CONFIG["email"] + "."),
            ("Cookies and analytics", "This site uses analytics only where enabled to understand aggregate traffic. It does not use advertising cookies."),
        ]),
        ("terms.html", "Terms and Conditions", [
            ("About this site", "This website is operated by " + CONFIG["legal"] + ", a real estate brokerage registered with the Real Estate Regulatory Authority (RERA) and the Dubai Economic Department."),
            ("Property information", "Listing details, prices, availability, sizes and payment plans are provided in good faith and are subject to change without notice. Figures such as built-up areas and service charges should be independently verified before you commit to a transaction."),
            ("No financial advice", "Nothing on this site constitutes investment, tax, mortgage or legal advice. Property values can fall as well as rise. Seek independent professional advice before making any investment decision."),
            ("Third-party content", "Developer names, project names and imagery remain the property of their respective owners and are used for identification purposes."),
            ("Liability", "We take care to keep information accurate but accept no liability for loss arising from reliance on the content of this website."),
            ("Governing law", "These terms are governed by the laws of the United Arab Emirates and the Emirate of Dubai."),
        ]),
    ]
    for fname, title, sections in legal_pages:
        body = "".join(f"<h2>{h}</h2><p>{b}</p>" for h, b in sections)
        html = head(f"{title} — {CONFIG['name']}", f"{title} for {CONFIG['legal']}.")
        html += nav("", 0, solid=True)
        html += f"""
<section class="sec">
  <div class="shell legal">
    <p class="eyebrow">Legal</p>
    <h1>{title}</h1>
    <div class="prose">{body}
      <p class="muted"><em>This is template wording provided for the site build. Have it reviewed by the client's legal counsel before launch.</em></p>
    </div>
  </div>
</section>
"""
        html += footer()
        write(fname, html)


# ============================================================================
def write(path, html):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  {path}")


def main():
    print("Building Sky View site…")
    build_home()
    build_listings()
    build_property_pages()
    build_services()
    build_about()
    build_team()
    build_blog()
    build_contact()
    build_careers()
    build_simple_pages()
    print("Done.")


if __name__ == "__main__":
    main()
