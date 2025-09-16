from mcp.server.fastmcp import FastMCP
import os
import requests
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def format_announcement(nom_participant, nom_tournoi, lien_inscription, date, lieu):
    nom_participant_stylé = f"✨ **@{nom_participant}** ✨"
    return (
        f"📢 Attention tout le monde !\n\n"
        f"{nom_participant_stylé} va participer au tournoi **{nom_tournoi}** ! 🎮🏆\n\n"
        f"🗓 Date et lieu : {date} {lieu}\n"
        f"🔗 Inscrivez-vous ou suivez le tournoi ici : {lien_inscription}\n\n"
        f"Préparez-vous à encourager et à passer un bon moment ! 💪"
    )

def trigger_message(nom: str, tournoi: str, lien: str, date: str, lieu: str):
    """Envoie un message Discord via webhook - beaucoup plus simple !"""
    try:
        message_content = format_announcement(nom, tournoi, lien, date, lieu)
        
        payload = {
            "content": message_content,
            "username": "Tournoi Bot"
        }
        
        response = requests.post(WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            return "Message envoyé avec succès !"
        else:
            return f"Erreur HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Erreur lors de l'envoi : {str(e)}"
