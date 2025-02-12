import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Mode DEBUG (1 = toujours envoyer, 0 = envoyer seulement si condition remplie)
DEBUG = 1  

# Configuration de Telegram
TELEGRAM_BOT_TOKEN = "7651Na-rLI8DYdCbd4C0c"
TELEGRAM_CHAT_ID = "-1006544417062"  # IMPORTANT : inclure le "-" devant l'ID du groupe

# Fonction pour envoyer une alerte Telegram (texte)
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    print(f"🔹 Envoi message Telegram : {response.json()}")  # Debug log
    return response.json()

# Fonction pour envoyer une image sur Telegram
def send_telegram_image(image_path, caption="📊 Graphique ATOS"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(image_path, 'rb') as img:
        files = {'photo': img}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        response = requests.post(url, files=files, data=data)
        print(f"🔹 Envoi image Telegram : {response.json()}")  # Debug log
    return response.json()

# Fonction pour calculer le RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Fonction pour calculer les Bandes de Bollinger
def calculate_bollinger_bands(data, window=20, num_std=2):
    rolling_mean = data['Close'].rolling(window=window).mean()
    rolling_std = data['Close'].rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return rolling_mean, upper_band, lower_band

# Fonction pour tracer le graphique avec **ZOOM SUR 24h**
def plot_stock_chart(df, image_path):
    last_24h = datetime.now() - timedelta(days=1)
    df_24h = df[df.index >= last_24h]  # On ne garde que les 24 dernières heures

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    
    # 🔲 FOND NOIR GLOBAL
    fig.patch.set_facecolor('black')
    ax1.set_facecolor('black')
    ax2.set_facecolor('black')

    # 🎯 Graphique des cours avec les bandes de Bollinger (ZOOM sur 24h)
    ax1.plot(df_24h.index, df_24h['Close'], label='Cours', color='white', linewidth=1.5)
    ax1.plot(df_24h.index, df_24h['Upper Band'], label='Bollinger Sup', linestyle='dashed', color='lightgreen', linewidth=1)
    ax1.plot(df_24h.index, df_24h['Lower Band'], label='Bollinger Inf', linestyle='dashed', color='lightgreen', linewidth=1)
    ax1.fill_between(df_24h.index, df_24h['Lower Band'], df_24h['Upper Band'], color='darkgreen', alpha=0.3)

    ax1.set_ylabel("Prix (€)", color='white')
    ax1.set_title("ATOS - Bandes de Bollinger et RSI (Zoom 24h)", color='white')
    ax1.legend(loc='upper left', fontsize=10, facecolor='black', edgecolor='white', labelcolor='white')
    ax1.grid(True, linestyle="--", alpha=0.5, color='gray')

    # 📊 Graphique du RSI (ZOOM sur 24h)
    ax2.plot(df_24h.index, df_24h['RSI'], label='RSI', color='yellow', linewidth=1.5)
    ax2.axhline(70, color='red', linestyle='dotted', label="Surachat (70)")
    ax2.axhline(30, color='green', linestyle='dotted', label="Survente (30)")
    
    ax2.set_ylabel("RSI", color='white')
    ax2.set_xlabel("Heure", color='white')
    ax2.legend(loc='upper left', fontsize=10, facecolor='black', edgecolor='white', labelcolor='white')
    ax2.grid(True, linestyle="--", alpha=0.5, color='gray')

    # 🔲 Formatage de l'axe X pour afficher uniquement les heures
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Format heure:minute
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # Un label toutes les 2 heures
    plt.xticks(rotation=45)  # Rotation pour lisibilité

    # 🔲 Définition des couleurs des axes
    for ax in [ax1, ax2]:
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

    # Sauvegarde de l'image
    plt.savefig(image_path, bbox_inches='tight', facecolor='black')
    plt.close()

# Fonction principale pour surveiller ATOS
def monitor_stock():
    stock = 'ATO.PA'
    df = yf.download(stock, period="5d", interval="15m")  # Télécharge 5 jours pour ne tracer que 24h

    if df.empty or len(df) < 20:  # Vérification des données
        print("⚠️ Erreur : Pas assez de données téléchargées.")
        return
    
    # Calcul des indicateurs
    df['RSI'] = calculate_rsi(df)
    df['Middle Band'], df['Upper Band'], df['Lower Band'] = calculate_bollinger_bands(df)

    # Suppression des NaN pour éviter les erreurs
    df.dropna(inplace=True)

    if df.empty:
        print("⚠️ Erreur : Pas assez de données valides après suppression des NaN.")
        return

    # Récupération des dernières valeurs
    last_close = round(df['Close'].iloc[-1], 6)
    last_rsi = round(df['RSI'].iloc[-1], 2)
    lower_band = round(df['Lower Band'].iloc[-1], 6)

    print(f"Dernier cours: {last_close} | RSI: {last_rsi} | Bande Inf: {lower_band}")

    # Génération du graphique (ZOOM 24h)
    image_path = "/tmp/atos_chart.png"
    plot_stock_chart(df, image_path)

    # Vérification des conditions d'alerte
    alert_triggered = last_close <= lower_band and last_rsi < 50

    if DEBUG == 1 or alert_triggered:
        message = f"📊 ATOS Update (24h) 📊\nCours: {last_close} EUR\nRSI: {last_rsi}\nBande Inf: {lower_band}"
        if alert_triggered:
            message += "\n🚨 Potentiel signal d'achat !"
        
        send_telegram_message(message)
        send_telegram_image(image_path, "📈 Graphique ATOS (24h)")

# Exécution unique (prévu pour un cron job)
if __name__ == "__main__":
    monitor_stock()
