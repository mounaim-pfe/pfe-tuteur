import streamlit as st
from openai import OpenAI
import csv
import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Tuteur IA PFE", page_icon="🎓")
st.title("🎓 Tuteur Socratique & Visuel")
st.markdown("Je suis ton coach. Si tu bloques, demande un indice !")

# --- GESTION DE LA CLÉ API (SECURE) ---
# Sur le Cloud, la clé sera cachée dans les "Secrets".
# En local, on regarde si elle est dans la barre latérale.
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Clé API OpenAI (Test local)", type="password")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Réglages")
    langue_choisie = st.selectbox("🗣️ Langue", ["Français", "العربية (Arabe)", "English", "Darija (Maroc)"])
    niveau = st.selectbox("🎓 Niveau", ["Primaire", "Collège", "Lycée", "Universitaire"])
    if st.button("🗑️ Reset"):
        st.session_state["messages"] = []
        st.rerun()

# --- CERVEAU (PROMPT) ---
if "Arabe" in langue_choisie:
    consigne_langue = "Réponds en Arabe littéraire."
elif "Darija" in langue_choisie:
    consigne_langue = "Réponds en Darija marocaine."
elif "English" in langue_choisie:
    consigne_langue = "Answer in English."
else:
    consigne_langue = "Réponds en Français."

system_prompt = f"""
Tu es un Tuteur Socratique BIENVEILLANT (Niveau {niveau}).
LANGUE : {consigne_langue}
RÈGLES :
1. Ne donne JAMAIS la réponse finale.
2. Guide par des questions.
3. Si l'élève est bloqué, donne un INDICE (analogie, exemple).
"""

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]
if st.session_state["messages"]:
    st.session_state["messages"][0]["content"] = system_prompt

# --- INTERFACE CHAT ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- BOUTON INDICE ---
col_aide, _ = st.columns([1, 3])
with col_aide:
    if st.button("💡 J'ai besoin d'un indice"):
        if not api_key:
            st.warning("Clé API manquante.")
        else:
            client = OpenAI(api_key=api_key)
            prompt_indice = "L'élève est bloqué. Donne un indice ou une analogie courte sans donner la réponse."
            ms_temp = st.session_state.messages.copy()
            ms_temp.append({"role": "system", "content": prompt_indice})
            with st.chat_message("assistant"):
                full_res = client.chat.completions.create(model="gpt-3.5-turbo", messages=ms_temp).choices[0].message.content
                st.write(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- ZONE DE SAISIE ---
if prompt := st.chat_input("Ta question..."):
    if not api_key:
        st.warning("Clé API manquante.")
        st.stop()
    client = OpenAI(api_key=api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages).choices[0].message.content
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- OUTILS FINAUX (BILAN + CARTE) ---
st.divider()
if len(st.session_state.messages) > 2:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Bilan Texte"):
            client = OpenAI(api_key=api_key)
            prompt_bilan = f"Fais un bilan structuré de la séance en {langue_choisie}."
            ms_bilan = st.session_state.messages.copy()
            ms_bilan.append({"role": "user", "content": prompt_bilan})
            res = client.chat.completions.create(model="gpt-3.5-turbo", messages=ms_bilan).choices[0].message.content
            st.info(res)
            
    with c2:
        if st.button("🗺️ Carte Mentale"):
            client = OpenAI(api_key=api_key)
            prompt_map = f"Génère UNIQUEMENT le code Graphviz DOT pour visualiser les concepts clés de cette conversation en {langue_choisie}."
            ms_map = st.session_state.messages.copy()
            ms_map.append({"role": "user", "content": prompt_map})
            code_dot = client.chat.completions.create(model="gpt-3.5-turbo", messages=ms_map).choices[0].message.content
            code_dot = code_dot.replace("```dot", "").replace("```", "").strip()
            try:
                st.graphviz_chart(code_dot)
            except:
                st.error("Erreur de génération visuelle.")