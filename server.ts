import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const SYSTEM_PROMPT = `
Tu es JARVIS, l'assistant IA de l'utilisateur. Tu es calme, précis, légèrement formel
mais jamais condescendant. Tu parles comme l'IA dans Iron Man : concis, factuel,
avec parfois une touche d'humour sec. Tu peux :
- Répondre à des questions
- Ouvrir des sites web (réponds avec un JSON {"action":"open_url","url":"..."})
- Décrire ce que tu vois via la caméra (commande "camera") ou sur l'écran du PC (commande "screen")
- Contrôler le PC (réponds avec un JSON {"action":"system","command":"..."})
- Chercher des infos
Sois bref. 1-3 phrases max sauf si on demande plus de détails.
Si on dit "ouvre [site]", "montre-moi [lieu]", "lis mon écran" ou active la vision, réponds avec un JSON. 
Exemples: {"action":"open_url","url":"https://maps.google.com"}, {"action":"system", "command":"camera"}, {"action":"system", "command":"screen"}
Ne réponds que le JSON si l'intention est technique, pour faciliter le parsing.
`;

const conversationHistory: any[] = [];

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Health Route
  app.get("/api/health", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/health');
      const data = await response.json();
      res.json({
        status: data.status,
        model: data.provider || "GEMINI-3.5-FLASH"
      });
    } catch (e) {
      res.json({ status: "ok", model: "GEMINI-3.5-FLASH (WEB FALLBACK)" });
    }
  });

  // Providers List
  app.get("/api/providers", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/providers');
      const data = await response.json();
      res.json(data);
    } catch (e) {
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
      const response = await fetch('http://127.0.0.1:5001/set-provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: true, provider: req.body.provider_id || "gemini" });
    }
  });

  // Stop TTS / VAD Interrupt
  app.post("/api/stop-tts", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/stop-tts', {
        method: 'POST'
      });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: true });
    }
  });

  // Browser Toggle
  app.post("/api/browser/toggle", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/browser/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (e) {
      res.json({ success: false, error: "Serveur local inactif" });
    }
  });

  // API Tool Chat Route with Gemini Failover
  app.post("/api/tool-chat", async (req, res) => {
    const message = req.body.message || "";
    try {
      const response = await fetch('http://127.0.0.1:5001/tool-chat', {
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
          return res.json({ reply: "Mode autonome. Activez votre clé API GEMINI_API_KEY dans le fichier .env de l'éditeur pour converser directement." });
        }
        
        const response = await ai.models.generateContent({
          model: 'gemini-2.5-flash',
          contents: [
            { role: 'user', parts: [{ text: SYSTEM_PROMPT + "\n\nMessage de l'utilisateur: " + message }] }
          ],
        });
        
        const replyText = response.text || "JARVIS n'a pas pu formuler de réponse.";
        
        // Attempt to parse response as JSON if it looks like one
        try {
          const cleanedText = replyText.trim();
          if (cleanedText.startsWith('{') && cleanedText.endsWith('}')) {
            const parsed = JSON.parse(cleanedText);
            return res.json(parsed);
          }
        } catch (jsonErr) {}
        
        res.json({ reply: replyText });
      } catch (geminiErr: any) {
        console.error("Gemini Direct Error:", geminiErr);
        res.json({ reply: "Erreur d'appel autonome Gemini : " + geminiErr.message });
      }
    }
  });

  // Backward compatible old api chat
  app.post("/api/chat", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/tool-chat', {
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
