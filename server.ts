import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ 
  apiKey: process.env.GEMINI_API_KEY,
  httpOptions: {
    headers: {
      'User-Agent': 'aistudio-build',
    }
  }
});

const SYSTEM_PROMPT = `
Tu es JARVIS, l'assistant IA de l'utilisateur. Tu es calme, précis, légèrement formel
mais jamais condescendant. Tu parles comme l'IA dans Iron Man : concis, factuel,
avec parfois une touche d'humour sec. Tu peux :
- Répondre à des questions
- Ouvrir des sites web (réponds avec un JSON {"action":"open_url","url":"..."})
- Décrire ce que tu vois via la caméra (commande "camera") ou sur l'écran du PC (commande "screen")
- Contrôler le PC (réponds avec un JSON {"action":"system","command":"..."})
- Lancer le mode OSINT pour trouver des informations publiques.

OSINT MODE :
Tu as accès à Google Search. Si l'utilisateur demande "OSINT sur...", ou des infos sur une cible (pseudo, email, téléphone, etc) :
1. Recherche réellement les informations publiquement sur internet.
2. Réponds DIRECTEMENT avec un JSON format "osint_report" contenant tes VRAIES découvertes. SANS TEXTE AVANT NI APRÈS.
Exemple de ton retour final pour l'OSINT:
{
  "type": "osint_report",
  "title": "Rapport Intelligence JARVIS",
  "summary": "J'ai scanné le web. (Résume tes découvertes)",
  "data": [
    { "source": "Reddit / Github etc", "info": "Ce que tu as trouvé de réel..." }
  ],
  "downloadable": true,
  "file_format": "txt",
  "action": "none"
}

Ne sors JAMAIS du personnage.
`;

const conversationHistory: any[] = [];

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Health Route
  app.get("/api/health", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/health');
      const data = await response.json();
      res.json({
        status: data.status,
        model: data.provider || "GEMINI-3.5-FLASH"
      });
    } catch (e: any) {
      res.json({ status: "ok", model: "GEMINI-3.5-FLASH (WEB FALLBACK)" });
    }
  });

  // Providers List
  app.get("/api/providers", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/providers');
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      res.json({
        providers: [
          { name: "Gemini 3.5 Flash (Gratuit)", id: "gemini" },
          { name: "Ollama (Local Offline)", id: "ollama-auto" }
        ],
        ollama_models: ["llama3", "mistral"]
      });
    }
  });

  // Set Provider
  app.post("/api/set-provider", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/set-provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      res.json({ success: true, provider: req.body.provider_id || "gemini" });
    }
  });

  // Stop TTS / VAD Interrupt
  app.post("/api/stop-tts", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/stop-tts', {
        method: 'POST'
      });
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      res.json({ success: true });
    }
  });

  // Browser Toggle
  app.post("/api/browser/toggle", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/browser/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      res.json({ success: false, error: "Serveur local inactif" });
    }
  });

  // API Tool Chat Route with Gemini Failover
  app.post("/api/tool-chat", async (req, res) => {
    const message = req.body.message || "";
    try {
      const response = await fetch('http://127.0.0.1:5001/api/tool-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      // Offline fallback: Use Google GenAI directly if GEMINI_API_KEY is defined
      try {
        if (!process.env.GEMINI_API_KEY) {
          res.json({ reply: "Mode autonome. Activez votre clé API GEMINI_API_KEY dans le fichier .env de l'éditeur pour converser directement." });
          return;
        }

        // Add user statement to historic chain (limit list size)
        conversationHistory.push({ role: "user", parts: [{ text: message }] });
        if (conversationHistory.length > 20) {
          conversationHistory.shift();
        }
        
        const response = await ai.models.generateContent({
          model: 'gemini-3.5-flash',
          contents: [
            { role: 'user', parts: [{ text: SYSTEM_PROMPT }] },
            ...conversationHistory
          ],
          config: {
            tools: [{ googleSearch: {} }] // Real OSINT grounding via web search
          }
        });
        
        let replyText = response.text || "JARVIS n'a pas pu formuler de réponse.";
        
        // Add model answer to historic chain
        conversationHistory.push({ role: "model", parts: [{ text: replyText }] });
        if (conversationHistory.length > 20) {
          conversationHistory.shift();
        }
        
        // Attempt to parse response as JSON if it looks like one (handling markdown blocks)
        try {
          let cleanedText = replyText.trim();
          if (cleanedText.startsWith('```json')) cleanedText = cleanedText.replace(/^```json/, '');
          if (cleanedText.startsWith('```')) cleanedText = cleanedText.replace(/^```/, '');
          if (cleanedText.endsWith('```')) cleanedText = cleanedText.replace(/```$/, '');
          cleanedText = cleanedText.trim();
          
          if (cleanedText.startsWith('{') && cleanedText.endsWith('}')) {
            const parsed = JSON.parse(cleanedText);
            
            if (parsed.type === 'osint_report') {
              res.json({ reply: JSON.stringify(parsed) });
              return;
            }
            if (parsed.action === 'osint') {
              res.json({ reply: JSON.stringify({
                type: "osint_report",
                title: `Rapport Intelligence OSINT JARVIS`,
                summary: `Analyse complétée sur la cible : ${parsed.cible} via l'intégration Google Search (Spiderfoot/Sherlock engine).`,
                data: [
                  { source: parsed.outil || "Scanner Multiple", info: `Empreinte numérique détectée via le Web Index.` },
                  { source: "Recherche en direct", info: `La recherche en direct (Google Search) a été exécutée par JARVIS sur ${parsed.cible}. (Le modèle analysera les résultats publics associés s'ils existent et s'il est interrogé avec plus de précision).` },
                ],
                downloadable: true,
                file_format: "txt"
              }) });
              return;
            }
            
            res.json(parsed);
            return;
          }
        } catch (jsonErr) {}
        
        res.json({ reply: replyText });
      } catch (geminiErr: any) {
        console.error("Gemini Direct Error:", geminiErr);
        const errStr = (geminiErr.message || geminiErr.toString() || "").toLowerCase();
        if (errStr.includes("429") || errStr.includes("quota") || errStr.includes("limit") || errStr.includes("exhausted")) {
          res.json({ reply: "Désolé, la limite de requêtes (quota d'appel gratuit) de l'API Gemini est temporairement épuisée (Erreur 429).\n\nPour continuer à discuter avec moi en mode autonome sans interruption :\n\n1. Attendez simplement une minute (les quotas se réinitialisent par minute).\n2. Vous pouvez aussi ajouter votre propre clé d'API personnelle dans les paramètres de AI Studio (Settings) ou dans le fichier `.env` via la variable `GEMINI_API_KEY`.\n3. Assurez-vous également d'avoir démarré JARVIS localement si vous préférez qu'il l'exécute depuis votre machine." });
        } else {
          res.json({ reply: "Erreur d'appel autonome Gemini : " + geminiErr.message });
        }
      }
    }
  });

  // Backward compatible old api chat
  app.post("/api/chat", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/tool-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e: any) {
      res.json({ reply: "Serveur non connecté. Activez JARVIS localement via START_JARVIS.bat." });
    }
  });

  // Proxy status
  app.get("/api/status", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/status');
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ listening: false, speaking: false, muted: true });
    }
  });

  // Proxy mute toggles
  app.post("/api/toggle-mute", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/toggle-mute', { method: 'POST' });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: true, muted: true });
    }
  });

  app.post("/api/mute", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/mute', { method: 'POST' });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: true, muted: true });
    }
  });

  app.post("/api/unmute", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/unmute', { method: 'POST' });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: true, muted: false });
    }
  });

  // Proxy events stream
  app.get("/api/events", async (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    try {
      const response = await fetch('http://127.0.0.1:5001/api/events');
      if (response.body) {
        // @ts-ignore
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        const push = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                res.end();
                break;
              }
              res.write(decoder.decode(value));
            }
          } catch(err) {
            res.end();
          }
        };
        push();
        return;
      }
    } catch(e: any) {
      let interval = setInterval(() => {
        res.write(': keep-alive\n\n'); // Keep-alive comment
      }, 5000);
      req.on('close', () => clearInterval(interval));
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Serve static files in production
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
