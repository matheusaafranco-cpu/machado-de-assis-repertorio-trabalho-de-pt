import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizRequest(BaseModel):
    tema: str = "Um Canário (Machado de Assis)"

@app.get("/", response_class=HTMLResponse)
def ler_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Portal do Machado de Assis</h1><p>index.html não encontrado no repositório.</p>"

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave GEMINI_API_KEY não configurada.")

    try:
        prompt_text = (
            f"Gere exatamente 3 perguntas de múltipla escolha inéditas e educativas sobre o conto '{req.tema}' de Machado de Assis. "
            "Retorne APENAS um JSON puro em formato de array, sem blocos de markdown, sem crases e sem texto adicional. "
            "Cada objeto do array deve ter estritamente esta estrutura:\n"
            "[\n"
            "  {\n"
            '    "question": "Texto da pergunta?",\n'
            '    "options": ["Opção A", "Opção B", "Opção C", "Opção D"],\n'
            '    "answer": 0,\n'
            '    "explanation": "Explicação detalhada da resposta correta."\n'
            "  }\n"
            "]"
        )

        # Endpoint oficial atualizado para a versão gratuita da API
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Limpeza rigorosa de crases e blocos caso a IA inclua
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            if clean_json.startswith("`"):
                clean_json = clean_json.strip("`").replace("json\n", "").strip()
                
            return json.loads(clean_json)
        else:
            print(f"Erro da API do Google: {response.text}")
            raise HTTPException(status_code=500, detail=f"Erro do Google: {response.text}")

    except Exception as e:
        print(f"Exceção ao comunicar com a IA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))