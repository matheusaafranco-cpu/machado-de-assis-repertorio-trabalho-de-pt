import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Permite que o front-end faça requisições sem bloqueio de CORS
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
    # Obtém a chave configurada no ambiente do Render
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave GEMINI_API_KEY não configurada no servidor.")

    prompt_text = (
        f"Gere 3 perguntas inéditas e criativas de múltipla escolha sobre o conto '{req.tema}' de Machado de Assis. "
        "Responda EXCLUSIVAMENTE com um JSON no formato de Array de objetos (sem markdown, sem ```json ou texto adicional). "
        "Estrutura obrigatória:\n"
        "[\n"
        "  {\n"
        '    "question": "Texto da pergunta?",\n'
        '    "options": ["Opção 0", "Opção 1", "Opção 2", "Opção 3"],\n'
        '    "answer": 0,\n'
        '    "explanation": "Explicação sobre a resposta correta."\n'
        "  }\n"
        "]\n"
        "O campo 'answer' deve ser um inteiro (0 a 3) indicando o índice da opção correta."
    )

    # Construção do URL dividida em blocos literais simples para evitar o erro da interface
    p1 = "https://"
    p2 = "generativelanguage.googleapis.com"
    p3 = "/v1beta/models/gemini-2.5-flash:generateContent?key="
    url = p1 + p2 + p3 + api_key

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Limpa marcas de código markdown caso a API retorne
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        
        quiz_json = json.loads(clean_json)
        return quiz_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar quiz: {str(e)}")