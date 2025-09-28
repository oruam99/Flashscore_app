from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
import os
from dotenv import load_dotenv

# 🔑 Carregar chave da API do ficheiro .env
load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}

# 🌐 Inicializar app e templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, jogo: str = Form(...)):
    """
    Recebe um jogo no formato "Equipa Casa vs Equipa Fora",
    vai buscar estatísticas reais à API, e sugere uma aposta simples.
    """
    # Validar formato do input
    try:
        home_team, away_team = [x.strip() for x in jogo.split("vs")]
    except ValueError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": "❌ Formato inválido. Usa: Equipa Casa vs Equipa Fora"
        })

    # 🔍 Função auxiliar para escolher equipa correta
    def escolher_equipe(data, nome):
        if "response" not in data or len(data["response"]) == 0:
            return None
        for t in data["response"]:
            if nome.lower() in t["team"]["name"].lower():
                return t
        return data["response"][0]  # fallback: primeira equipa

    try:
        # Buscar equipas
        home_resp = requests.get(f"https://v3.football.api-sports.io/teams?name={home_team}", headers=HEADERS)
        away_resp = requests.get(f"https://v3.football.api-sports.io/teams?name={away_team}", headers=HEADERS)
        home_data = home_resp.json()
        away_data = away_resp.json()

        # Escolher equipas corretas
        home_team_data = escolher_equipe(home_data, home_team)
        away_team_data = escolher_equipe(away_data, away_team)

        if home_team_data is None or away_team_data is None:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "resultado": "❌ Equipa(s) não encontrada(s). Verifica os nomes."
            })

        home_id = home_team_data["team"]["id"]
        away_id = away_team_data["team"]["id"]
        home_name = home_team_data["team"]["name"]
        away_name = away_team_data["team"]["name"]

        # ⚽ Obter estatísticas (últimos 5 jogos na liga principal)
        # Nota: podes mudar o league_id para a liga que quiseres
        league_id = 39  # exemplo: Premier League
        season = 2024

        home_stats_resp = requests.get(
            f"https://v3.football.api-sports.io/teams/statistics?team={home_id}&season={season}&league={league_id}",
            headers=HEADERS
        )
        away_stats_resp = requests.get(
            f"https://v3.football.api-sports.io/teams/statistics?team={away_id}&season={season}&league={league_id}",
            headers=HEADERS
        )

        home_stats = home_stats_resp.json()
        away_stats = away_stats_resp.json()

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": f"❌ Erro ao obter dados da API: {str(e)}"
        })

    # 📊 Extrair estatísticas simples
    try:
        home_wins = home_stats["response"]["fixtures"]["wins"]["total"]
        away_wins = away_stats["response"]["fixtures"]["wins"]["total"]

        home_draws = home_stats["response"]["fixtures"]["draws"]["total"]
        away_draws = away_stats["response"]["fixtures"]["draws"]["total"]

        home_losses = home_stats["response"]["fixtures"]["loses"]["total"]
        away_losses = away_stats["response"]["fixtures"]["loses"]["total"]
    except KeyError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": "⚠️ Estatísticas não encontradas para estas equipas/temporada."
        })

    # 🧠 Sugestão de aposta simples
    if home_wins > away_wins + 3:
        sugestao = f"🏠 Apostar na vitória do {home_name} parece seguro."
    elif away_wins > home_wins + 3:
        sugestao = f"🚀 Apostar na vitória do {away_name} pode ser uma boa."
    else:
        sugestao = "🤝 Jogo equilibrado — aposta em empate ou dupla hipótese."

    resultado = (
        f"📊 {home_name}: {home_wins}V / {home_draws}E / {home_losses}D\n"
        f"📊 {away_name}: {away_wins}V / {away_draws}E / {away_losses}D\n\n"
        f"💡 Sugestão: {sugestao}"
    )

    return templates.TemplateResponse("index.html", {"request": request, "resultado": resultado})
