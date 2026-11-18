"""
MLDisLSTMTHREAD3 - Complementary Datasets Generator
Creates:
1. data/safety_nlp_corpus.csv (Annotated safety & distress messages for DistilBERT)
2. data/delhi_safety_poi.csv (Real urban Police Stations, Women Help Desks & Hospitals)
3. data/sample_crowdsourced_reports.csv (Community safety incident reports with timestamps)
"""

import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# 1. NLP Safety Corpus for DistilBERT Fine-Tuning
# -------------------------------------------------------------
def create_safety_nlp_corpus():
    corpus = [
        # Normal (0) - Daily commute, chatting, safe arrivals
        ("Reached my PG hostel safely, locked the door.", 0, "Normal"),
        ("I am on the metro yellow line, sitting in the ladies coach.", 0, "Normal"),
        ("Traffic is quite heavy near the flyover, will reach in 30 mins.", 0, "Normal"),
        ("Boarded the DTC bus 534 from Lajpat Nagar.", 0, "Normal"),
        ("Having dinner with my college roommates at the cafe.", 0, "Normal"),
        ("Just booked an Uber cab, driver name Ramesh, cab number 4821.", 0, "Normal"),
        ("Walking towards the campus library with my friend.", 0, "Normal"),
        ("Street is well lit and crowded with evening shoppers.", 0, "Normal"),
        ("Train has reached platform 4, deboarding now.", 0, "Normal"),
        ("Office meeting finished, heading towards the parking lot.", 0, "Normal"),
        ("Mom I have reached Bangalore airport terminal 1 safely.", 0, "Normal"),
        ("Auto rickshaw driver is following Google Maps route properly.", 0, "Normal"),
        ("Waiting for my father to pick me up from the metro station.", 0, "Normal"),
        ("Bus conductor gave me a ladies seat in the front row.", 0, "Normal"),
        ("Walking through the main market road, lots of street vendors here.", 0, "Normal"),
        ("Shared my live location with you on WhatsApp.", 0, "Normal"),
        ("Reached the coaching institute, class starts in 10 minutes.", 0, "Normal"),
        ("Taking the skywalk towards the residential gate.", 0, "Normal"),
        ("Everything looks fine here, nothing to worry about.", 0, "Normal"),
        ("Entered the apartment building, taking the lift now.", 0, "Normal"),

        # Suspicious (1) - Loitering, tailing, unlit alleys, unexpected detours
        ("A black car has been driving very slowly behind me for 3 streets.", 1, "Suspicious"),
        ("Two men are standing near the dark corner watching every pedestrian.", 1, "Suspicious"),
        ("Someone is loitering near my hostel gate looking around nervously.", 1, "Suspicious"),
        ("A guy on a scooter passed by three times looking straight at me.", 1, "Suspicious"),
        ("I feel like I am being followed since I stepped out of the station.", 1, "Suspicious"),
        ("The cab driver took a strange turn into an unlit narrow dirt lane.", 1, "Suspicious"),
        ("A group of men are staring and matching my walking pace.", 1, "Suspicious"),
        ("All the streetlights are completely off and someone is walking quietly behind me.", 1, "Suspicious"),
        ("The auto driver turned off the meter and refused to take the main road.", 1, "Suspicious"),
        ("A stranger followed me from the bus stop into the residential alley.", 1, "Suspicious"),
        ("A man is standing right outside my building entrance watching my window.", 1, "Suspicious"),
        ("A bike without a number plate has stopped 20 meters ahead of me.", 1, "Suspicious"),
        ("Someone is pacing back and forth outside the ATM booth while I am inside.", 1, "Suspicious"),
        ("The driver keeps looking at me repeatedly in the rear-view mirror.", 1, "Suspicious"),
        ("A guy got down from the bus right behind me and is walking in my shadow.", 1, "Suspicious"),
        ("The dark pathway through the park feels very unsafe right now.", 1, "Suspicious"),
        ("Two individuals are whispering and pointing towards me near the overbridge.", 1, "Suspicious"),
        ("A van has parked beside the footpath with engine running and headlights off.", 1, "Suspicious"),
        ("Someone is tracking my footsteps in the staircase.", 1, "Suspicious"),
        ("An unknown person is lingering around my parked car.", 1, "Suspicious"),

        # Harassment (2) - Stalking, catcalling, verbal intimidation, non-consensual contact
        ("A man is catcalling and shouting vulgar comments at the bus stop.", 2, "Harassment"),
        ("Someone just grabbed my arm and tried to block my pathway!", 2, "Harassment"),
        ("A stranger is aggressively demanding my phone number and refuses to leave.", 2, "Harassment"),
        ("Two men on a bike whistled and made obscene hand gestures as they passed.", 2, "Harassment"),
        ("A guy followed me inside the elevator and made inappropriate sexual remarks.", 2, "Harassment"),
        ("He blocked the narrow lane and is threatening me if I scream.", 2, "Harassment"),
        ("A man on a scooter tried to touch my shoulder while speeding past.", 2, "Harassment"),
        ("They are passing filthy comments outside my door and laughing.", 2, "Harassment"),
        ("Someone is taking photos of me without consent on the bus.", 2, "Harassment"),
        ("He pulled my backpack strap and whispered abusive words in my ear.", 2, "Harassment"),
        ("A drunk guy is shouting vulgarities and following me down the street.", 2, "Harassment"),
        ("Two men blocked the sidewalk and are laughing while trapping me.", 2, "Harassment"),
        ("He keeps nudging against me on the crowded metro deliberately.", 2, "Harassment"),
        ("A man opened his car window and shouted lewd sexual propositions at me.", 2, "Harassment"),
        ("He flashed himself near the dark corner of the underpass!", 2, "Harassment"),
        ("A guy grabbed my dupatta and tried to drag me backwards!", 2, "Harassment"),
        ("Someone is persistently stalking me every evening from work to home.", 2, "Harassment"),
        ("He cornered me near the vending machine and won't let me pass.", 2, "Harassment"),
        ("Two youths are hurling aggressive sexual slurs outside the hostel.", 2, "Harassment"),
        ("A man is knocking aggressively on my cab window at the red light.", 2, "Harassment"),

        # Emergency (3) - Imminent physical violence, abduction, weapons, acute danger
        ("HELP ME! I am being attacked near the park entrance, send police now!", 3, "Emergency"),
        ("EMERGENCY! Someone is trying to force me into a van! PLEASE HURRY!", 3, "Emergency"),
        ("I am trapped in a room and someone is banging violently on the door, HELP!", 3, "Emergency"),
        ("SOS! He has a knife and is threatening to kill me! Send help immediately!", 3, "Emergency"),
        ("Help me please! I am bleeding and hiding behind the petrol pump!", 3, "Emergency"),
        ("HE IS ATTACKING ME! SEND POLICE TO NEAR METRO PILLAR 42 NOW!", 3, "Emergency"),
        ("EMERGENCY SOS! Kidnapping attempt in progress, send police right now!", 3, "Emergency"),
        ("I need urgent help, someone broke the window and entered my flat!", 3, "Emergency"),
        ("SOS! Being physically assaulted in the alleyway, can't escape!", 3, "Emergency"),
        ("HELP! Physical violence underway, immediate police intervention needed!", 3, "Emergency"),
        ("HE HAS CORNERED ME WITH A WEAPON! SEND IMMEDIATE HELP TO PARK STREET!", 3, "Emergency"),
        ("HELP! MY CAB DRIVER HAS LOCKED THE DOORS AND IS SPEEDING AWAY TOWARDS THE JUNGLE!", 3, "Emergency"),
        ("SOS EMERGENCY! Someone is choking me, please send police right away!", 3, "Emergency"),
        ("HE IS DRAGGING ME INTO AN ABANDONED BUILDING! HELP PLEASE!", 3, "Emergency"),
        ("EMERGENCY! I AM BEING PHYSICALLY ATTACKED BY THREE MEN, SEND HELP FAST!", 3, "Emergency"),
        ("HELP ME! I am hiding inside the washroom, they are trying to break the lock!", 3, "Emergency"),
        ("SOS! Armed assault in progress, please dispatch police to Connaught Place block B!", 3, "Emergency"),
        ("HE HIT ME ON THE HEAD AND IS TRYING TO ABDUCT ME, EMERGENCY POLICE NEEDED!", 3, "Emergency"),
        ("HELP SOS! VIOLENT ATTACK IN PROGRESS NEAR THE SUBWAY EXIT!", 3, "Emergency"),
        ("SEND POLICE IMMEDIATELY! LIFE THREATENING DISTRESS AT SECTOR 62!", 3, "Emergency")
    ]
    
    # Expand corpus with realistic variations to create a robust dataset of 320+ samples
    expanded_rows = []
    modifiers = [
        "", "Please hurry. ", "Happening right now. ", "Very scared. ",
        "Near the main road. ", "At the metro station. ", "Outside the office building. "
    ]
    
    for text, label, cat_name in corpus:
        expanded_rows.append({"text": text, "label": label, "category": cat_name})
        # Add varied formulations
        for mod in modifiers[1:4]:
            expanded_rows.append({
                "text": (mod + text).strip(),
                "label": label,
                "category": cat_name
            })
            
    df_nlp = pd.DataFrame(expanded_rows)
    out_file = DATA_DIR / "safety_nlp_corpus.csv"
    df_nlp.to_csv(out_file, index=False)
    print(f"[Dataset 1] Generated NLP corpus ({len(df_nlp)} annotated texts) -> {out_file}")


# -------------------------------------------------------------
# 2. Real Delhi/NCR Safety Points of Interest (POI)
# -------------------------------------------------------------
def create_safety_poi():
    poi_data = [
        # Police Stations & Women Help Desks
        {"name": "Parliament Street Police Station", "type": "Police_Station", "latitude": 28.6256, "longitude": 77.2144, "has_women_helpdesk": True},
        {"name": "Connaught Place Police Station", "type": "Police_Station", "latitude": 28.6328, "longitude": 77.2197, "has_women_helpdesk": True},
        {"name": "Hauz Khas Police Station", "type": "Police_Station", "latitude": 28.5494, "longitude": 77.2001, "has_women_helpdesk": True},
        {"name": "Karol Bagh Police Station", "type": "Police_Station", "latitude": 28.6514, "longitude": 77.1907, "has_women_helpdesk": True},
        {"name": "Kashmere Gate Police Station", "type": "Police_Station", "latitude": 28.6675, "longitude": 77.2285, "has_women_helpdesk": True},
        {"name": "Saket Police Station", "type": "Police_Station", "latitude": 28.5244, "longitude": 77.2066, "has_women_helpdesk": True},
        {"name": "Dwarka South Police Station", "type": "Police_Station", "latitude": 28.5729, "longitude": 77.0691, "has_women_helpdesk": True},
        {"name": "Rohini North Police Station", "type": "Police_Station", "latitude": 28.7166, "longitude": 77.1147, "has_women_helpdesk": True},
        {"name": "Noida Sector 20 Police Station", "type": "Police_Station", "latitude": 28.5783, "longitude": 77.3328, "has_women_helpdesk": True},
        {"name": "Gurugram DLF Phase 1 Police Station", "type": "Police_Station", "latitude": 28.4732, "longitude": 77.0982, "has_women_helpdesk": True},
        
        # 24/7 Emergency Medical Hospitals
        {"name": "AIIMS Trauma Centre", "type": "Hospital_Emergency", "latitude": 28.5672, "longitude": 77.2100, "has_women_helpdesk": True},
        {"name": "Safdarjung Hospital Emergency", "type": "Hospital_Emergency", "latitude": 28.5694, "longitude": 77.2078, "has_women_helpdesk": True},
        {"name": "Ram Manohar Lohia Hospital", "type": "Hospital_Emergency", "latitude": 28.6247, "longitude": 77.2014, "has_women_helpdesk": True},
        {"name": "Lok Nayak Hospital (LNJP)", "type": "Hospital_Emergency", "latitude": 28.6385, "longitude": 77.2405, "has_women_helpdesk": False},
        {"name": "Max Super Speciality Hospital Saket", "type": "Hospital_Emergency", "latitude": 28.5276, "longitude": 77.2140, "has_women_helpdesk": True},
        {"name": "Fortis Escorts Heart Institute Okhla", "type": "Hospital_Emergency", "latitude": 28.5601, "longitude": 77.2797, "has_women_helpdesk": False},
        {"name": "Sir Ganga Ram Hospital", "type": "Hospital_Emergency", "latitude": 28.6387, "longitude": 77.1895, "has_women_helpdesk": False},
        {"name": "Medanta The Medicity Gurugram", "type": "Hospital_Emergency", "latitude": 28.4395, "longitude": 77.0425, "has_women_helpdesk": True}
    ]
    df_poi = pd.DataFrame(poi_data)
    out_file = DATA_DIR / "delhi_safety_poi.csv"
    df_poi.to_csv(out_file, index=False)
    print(f"[Dataset 2] Generated Safety POI registry ({len(df_poi)} locations) -> {out_file}")


# -------------------------------------------------------------
# 3. Sample Crowdsourced Incident Feed with Recency
# -------------------------------------------------------------
def create_sample_crowdsourced_feed():
    now = datetime.now(timezone.utc)
    reports = [
        {
            "report_id": "REP_001",
            "latitude": 28.6330, "longitude": 77.2199,
            "incident_type": "Poor_Lighting_Dark",
            "verification_status": "community_confirmed",
            "upvotes": 7,
            "timestamp": (now - timedelta(minutes=25)).isoformat()
        },
        {
            "report_id": "REP_002",
            "latitude": 28.6315, "longitude": 77.2180,
            "incident_type": "Stalking_Following",
            "verification_status": "verified_official",
            "upvotes": 14,
            "timestamp": (now - timedelta(minutes=45)).isoformat()
        },
        {
            "report_id": "REP_003",
            "latitude": 28.5490, "longitude": 77.2010,
            "incident_type": "Harassment_Physical",
            "verification_status": "community_confirmed",
            "upvotes": 5,
            "timestamp": (now - timedelta(hours=3)).isoformat()
        },
        {
            "report_id": "REP_004",
            "latitude": 28.5240, "longitude": 77.2060,
            "incident_type": "Verbal_Abuse",
            "verification_status": "unverified",
            "upvotes": 1,
            "timestamp": (now - timedelta(hours=7)).isoformat()
        },
        {
            "report_id": "REP_005",
            "latitude": 28.5780, "longitude": 77.3320,
            "incident_type": "SOS_Distress",
            "verification_status": "verified_official",
            "upvotes": 22,
            "timestamp": (now - timedelta(minutes=10)).isoformat()
        }
    ]
    df_rep = pd.DataFrame(reports)
    out_file = DATA_DIR / "sample_crowdsourced_reports.csv"
    df_rep.to_csv(out_file, index=False)
    print(f"[Dataset 3] Generated Crowdsourced Safety Reports ({len(df_rep)} records) -> {out_file}")


if __name__ == "__main__":
    create_safety_nlp_corpus()
    create_safety_poi()
    create_sample_crowdsourced_feed()
    print("All complementary datasets generated successfully inside MLDisLSTMTHREAD3/data/!")
