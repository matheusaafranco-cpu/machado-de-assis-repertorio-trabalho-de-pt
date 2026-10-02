@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada no Render.")

    try:
        client = Groq(api_key=api_key)

        prompt_text = (
            f"Gere exatamente 3 perguntas de múltipla escolha inéditas e educativas sobre o conto '{req.tema}' de Machado de Assis. "
            "Retorne APENAS um JSON puro em formato de array, sem blocos de markdown e sem texto adicional. "
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

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "És um assistente especializado em literatura que devolve estritamente JSON puro."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7
        )
        
        raw_text = completion.choices[0].message.content
        
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        if clean_json.startswith("`"):
            clean_json = clean_json.strip("`").replace("json\n", "").strip()
            
        return json.loads(clean_json)

    except Exception as e:
        print(f"Exceção ao comunicar com a Groq: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))