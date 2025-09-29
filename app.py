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
    busca estatísticas reais à API, e sugere uma aposta simples.
    Funciona para qualquer país.
    """
    # Validar formato do input
    try:
        home_team, away_team = [x.strip() for x in jogo.split("vs")]
    except ValueError:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": "❌ Formato inválido. Usa: Equipa Casa vs Equipa Fora"
        })

    # 🔍 Obter IDs das equipas (qualquer país)
    try:
        def get_team_id(team_name):
            resp = requests.get(f"https://v3.football.api-sports.io/teams?name={team_name}", headers=HEADERS)
            data = resp.json()
            if "response" not in data or not data["response"]:
                return None
            # Escolhe a primeira equipa retornada (pode ser aprimorado para filtrar por país/league)
            return data["response"][0]["team"]["id"], data["response"][0]["team"]["name"]

        home_info = get_team_id(home_team)
        away_info = get_team_id(away_team)

        if not home_info or not away_info:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "resultado": "❌ Equipa(s) não encontrada(s). Verifica os nomes."
            })

        home_id, home_name = home_info
        away_id, away_name = away_info

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": f"❌ Erro ao obter dados da API: {str(e)}"
        })

    # 📊 Obter estatísticas simples (últimos 5 jogos de cada equipa)
    try:
        def get_stats(team_id):
            resp = requests.get(
                f"https://v3.football.api-sports.io/teams/statistics?team={team_id}",
                headers=HEADERS
            )
            data = resp.json()
            if "response" not in data:
                return None
            stats = data["response"]["fixtures"]
            wins = stats.get("wins", {}).get("total", 0)
            draws = stats.get("draws", {}).get("total", 0)
            loses = stats.get("loses", {}).get("total", 0)
            return wins, draws, loses

        home_wins, home_draws, home_losses = get_stats(home_id)
        away_wins, away_draws, away_losses = get_stats(away_id)

    except Exception:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "resultado": "⚠️ Estatísticas não disponíveis para estas equipas."
        })

    # 🧠 Lógica simples de sugestão de aposta
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
