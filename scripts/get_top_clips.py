# scripts/get_top_clips.py
import requests
import os
import json
import sys
from datetime import datetime, timedelta, timezone

# Twitch API credentials from GitHub Secrets
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERREUR: TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET non définis.")
    sys.exit(1)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix/clips"

# --- PARAMÈTRES DE FILTRAGE ET DE SÉLECTION POUR LES SHORTS ---

# Ces paramètres de priorisation et de limite par streamer sont déplacés ou simplifiés
# car la logique de sélection finale est maintenant dans main.py qui va itérer sur cette liste complète.
# PRIORITIZE_BROADCASTERS_STRICTLY = False # Peut être supprimé ou ignoré
# MAX_CLIPS_PER_BROADCASTER_IN_FINAL_SELECTION = 1 # Peut être supprimé ou ignoré

# Liste des IDs de jeux pour lesquels vous voulez récupérer des clips.
GAME_IDS = [
    "509670",            # Just Chatting
    "21779",             # League of Legends
    "32982",             # Grand Theft Auto V
    "512965",            # VALORANT
    "518018",            # Minecraft
    "513143",            # Fortnite
    "32982",             # Grand Theft Auto V
    "32399",             # Counter-Strike
    "511224",            # Apex Legends
    "506520",            # Dota 2
    "490422",            # Dead by Daylight
    "514873",            # Call of Duty: Warzone
    "65768",             # Rocket League
    "518883",            # EA Sports FC 24
    "180025139",         # Mario Kart 8 Deluxe
    "280721",            # Teamfight Tactics
    "488427",            # World of Warcraft
    "1467408070",        # Rust
    "32213",             # Hearthstone
    "138585",            # Chess
    "493306",            # Overwatch 2
    "509660",            # Special Events
    "1063683693",        # Pokémon Scarlet and Violet
    "1678120671",        # Baldur's Gate 3
    "27471",             # osu!
    "507316",            # Phasmophobia
    "19326",             # The Elder Scrolls V: Skyrim
    "512710",            # Fall Guys
    "1285324545",        # Lethal Company
    # Ajoutez d'autres IDs si nécessaire
]

# Liste des IDs de streamers francophones populaires.
BROADCASTER_IDS = [
    "80716629",          # Inoxtag
    "737048563",         # Anyme023"
    "52130765",          # Squeezie (chaîne principale)
    "22245231",          # SqueezieLive (sa chaîne secondaire pour le live)
    "41719107",          # ZeratoR
    "24147592",          # Gotaga
    "134966333",         # Kameto
    "737048563",         # AmineMaTue
    "496105401",         # byilhann
    "887001013",         # Nico_la
    "60256640",          # Flamby
    "253195796",         # helydia
    "175560856",         # Hctuan
    "57404419",          # Ponce
    "38038890",          # Antoine Daniel
    "48480373",          # MisterMV
    "19075728",          # Sardoche
    "54546583",          # Locklear
    "50290500",          # Domingo
    "57402636",          # RebeuDeter
    "47565457",          # Joyca
    "153066440",         # Michou
    "41487980",          # Pauleta_Twitch (Pfut)
    "31429949",          # LeBouseuh
    "46296316",          # Maghla
    "49896798",          # Chowh1
    "49749557",          # Jiraya
    "53696803",          # Wankil Studio (Laink et Terracid - chaîne principale)
    "72366922",          # Laink (ID individuel, généralement couvert par Wankil Studio)
    "129845722",         # Terracid (ID individuel, généralement couvert par Wankil Studio)
    "51950294",          # Mynthos
    "53140510",          # Etoiles
    "134812328",         # LittleBigWhale
    "180237751",         # Mister V (l'artiste/youtubeur, différent de MisterMV)
    "55787682",          # Shaunz
    "142436402",         # Ultia
    "20875990",          # LCK_France (pour les clips de la ligue de LoL française)
    # Ajoutez d'autres IDs vérifiés ici
]

# --- NOUVEAU PARAMÈTRE : Langue du clip ---
CLIP_LANGUAGE = "fr" # Code ISO 639-1 pour le français

# PARAMÈTRES POUR LA DURÉE CUMULÉE MINIMALE ET MAXIMALE DU SHORT FINAL
MIN_VIDEO_DURATION_SECONDS = 15   # Minimum 15 secondes pour un Short
MAX_VIDEO_DURATION_SECONDS = 180  # Maximum 180 secondes (3 minutes) pour un Short

# --- FIN PARAMÈTRES ---

def get_twitch_access_token():
    """Gets an application access token for Twitch API."""
    print("🔑 Récupération du jeton d'accès Twitch...")
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(TWITCH_AUTH_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        print("✅ Jeton d'accès Twitch récupéré.")
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération du jeton d'accès Twitch : {e}")
        sys.exit(1)

def fetch_clips(access_token, params, source_type, source_id):
    """Helper function to fetch clips and handle errors."""
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(TWITCH_API_URL, headers=headers, params=params)
        response.raise_for_status()
        clips_data = response.json()
        
        if not clips_data.get("data"):
            print(f"  ⚠️ Aucune donnée de clip trouvée pour {source_type} {source_id} dans la période spécifiée.")
            return []

        collected_clips = []
        for clip in clips_data.get("data", []):
            collected_clips.append({
                "id": clip.get("id"),
                "url": clip.get("url"),
                "embed_url": clip.get("embed_url"),
                "thumbnail_url": clip.get("thumbnail_url"),
                "title": clip.get("title"),
                # CORRECTION ICI: Utilise "view_count" au lieu de "viewer_count"
                "viewer_count": clip.get("view_count", 0),  # Clé correcte de l'API Twitch
                "broadcaster_id": clip.get("broadcaster_id"),
                "broadcaster_name": clip.get("broadcaster_name"),
                "game_name": clip.get("game_name"),
                "created_at": clip.get("created_at"),
                "duration": float(clip.get("duration", 0.0)),
                "language": clip.get("language")
            })
        return collected_clips
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des clips Twitch pour {source_type} {source_id} : {e}")
        if response.content:
            print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de décodage JSON pour {source_type} {source_id}: {e}")
        if response.content:
            print(f"    Contenu brut de la réponse: {response.content.decode()}")
        return []

def get_eligible_short_clips(access_token, num_clips_per_source=50, days_ago=1, already_published_clip_ids=None):
    """
    Récupère les clips populaires des chaînes spécifiées et des jeux,
    filtre ceux déjà publiés et ceux qui ne respectent pas les contraintes de durée/langue.
    Retourne une liste de clips éligibles, triés par popularité (vues).
    """
    if already_published_clip_ids is None:
        already_published_clip_ids = []

    print(f"📊 Recherche de clips éligibles ({MIN_VIDEO_DURATION_SECONDS}-{MAX_VIDEO_DURATION_SECONDS}s) pour les dernières {days_ago} jour(s)...")
    print(f"Clips déjà publiés aujourd'hui (transmis) : {len(already_published_clip_ids)} IDs.")
            
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
            
    # Utilise un set pour une recherche rapide et pour éviter les doublons lors de la collecte
    seen_clip_ids = set(already_published_clip_ids) 
    all_potential_clips = []

    # --- Phase de collecte ---
    # Collecte des clips des broadcasters
    print("\n--- Collecte des clips des streamers spécifiés ---")
    for broadcaster_id in BROADCASTER_IDS:
        # print(f"  - Recherche de clips pour le streamer: {broadcaster_id}") # Moins verbeux
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "broadcaster_id": broadcaster_id,
            "language": CLIP_LANGUAGE
        }
        clips = fetch_clips(access_token, params, "broadcaster_id", broadcaster_id)
        for clip in clips:
            # Filtrer par langue et durée dès la collecte pour optimiser
            if (clip["id"] not in seen_clip_ids and 
                clip.get('language') == CLIP_LANGUAGE and
                MIN_VIDEO_DURATION_SECONDS <= clip.get('duration', 0.0) <= MAX_VIDEO_DURATION_SECONDS):
                all_potential_clips.append(clip)
                seen_clip_ids.add(clip["id"]) # Ajoute à 'seen' pour éviter les doublons globaux
    print(f"✅ Collecté {len(all_potential_clips)} clips uniques éligibles (streamers).")

    # Collecte des clips des jeux (excluant ceux déjà vus des broadcasters et déjà publiés)
    print("\n--- Collecte des clips des jeux spécifiés ---")
    for game_id in GAME_IDS:
        # print(f"  - Recherche de clips pour le jeu: {game_id}") # Moins verbeux
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id,
            "language": CLIP_LANGUAGE
        }
        clips = fetch_clips(access_token, params, "game_id", game_id)
        for clip in clips:
            # Filtrer par langue et durée dès la collecte pour optimiser
            if (clip["id"] not in seen_clip_ids and 
                clip.get('language') == CLIP_LANGUAGE and
                MIN_VIDEO_DURATION_SECONDS <= clip.get('duration', 0.0) <= MAX_VIDEO_DURATION_SECONDS):
                all_potential_clips.append(clip)
                seen_clip_ids.add(clip["id"])
    print(f"✅ Collecté un total de {len(all_potential_clips)} clips uniques éligibles (streamers + jeux).")

    # Trier tous les clips éligibles par vues (plus populaire en premier)
    all_potential_clips.sort(key=lambda x: x.get('viewer_count', 0), reverse=True)

    if not all_potential_clips:
        print(f"⚠️ Aucun clip éligible trouvé après collecte et filtrage (durée entre {MIN_VIDEO_DURATION_SECONDS} et {MAX_VIDEO_DURATION_SECONDS}s, non publié).")
        return [] # Retourne une liste vide
    else:
        print(f"Found {len(all_potential_clips)} clips éligibles au total, triés par vues.")
        # Optionnel: afficher le top 5 des candidats pour débogage
        # print("Top 5 candidats:")
        # for i, clip in enumerate(all_potential_clips[:5]):
        #     print(f"  {i+1}. {clip['title']} par {clip['broadcaster_name']} ({clip['viewer_count']} vues, {clip['duration']}s)")

    return all_potential_clips

# Le bloc if __name__ == "__main__": peut être laissé tel quel ou simplifié pour un test rapide
if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        # Simule l'historique de publication pour le test
        published_clips_log_path = os.path.join("data", "published_shorts_history.json")
        current_published_ids = []
        if os.path.exists(published_clips_log_path):
            try:
                with open(published_clips_log_path, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    today_str = datetime.now(timezone.utc).date().isoformat()
                    if today_str in history_data:
                        current_published_ids = [item["twitch_clip_id"] for item in history_data[today_str]]
            except json.JSONDecodeError:
                print("⚠️ Fichier d'historique des publications corrompu ou vide. Utilisation d'un historique vide.")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de l'historique simulé : {e}")

        eligible_clips_list = get_eligible_short_clips(
            access_token=token,
            num_clips_per_source=50,
            days_ago=1,
            already_published_clip_ids=current_published_ids
        )

        if eligible_clips_list:
            print(f"\n✅ {len(eligible_clips_list)} clip(s) éligible(s) trouvé(s) pour les Shorts.")
            print("Premier clip suggéré :")
            selected_clip = eligible_clips_list[0]
            print(f"  Titre: {selected_clip.get('title', 'N/A')}")
            print(f"  Streamer: {selected_clip.get('broadcaster_name', 'N/A')}")
            print(f"  Vues: {selected_clip.get('viewer_count', 0)}")
            print(f"  Durée: {selected_clip.get('duration', 'N/A')}s")
            print(f"  URL: {selected_clip.get('url', 'N/A')}")
        else:
            print("\n❌ Aucun clip approprié n'a pu être trouvé pour le Short cette fois.")