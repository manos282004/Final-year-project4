import { useState, useRef, useEffect } from "react";
import { Send, Bot, Loader2, Plus, Trash2 } from "lucide-react";
import { apiService } from "../services/api";
import type { LocationData } from "../services/api";

type Props = {
  businessType?: string;
  onLocationSelect?: (location: LocationData) => void;
  onLocationsUpdate?: (locations: LocationData[]) => void;
};

export default function Chatbot({
  businessType,
  onLocationSelect,
  onLocationsUpdate,
}: Props) {
  const [messages, setMessages] = useState<any[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* ===============================
     Session Init
  ================================ */
  useEffect(() => {
    let storedSessionId = localStorage.getItem("chat_session_id");
    if (!storedSessionId) {
      storedSessionId = crypto.randomUUID();
      localStorage.setItem("chat_session_id", storedSessionId);
    }
    setSessionId(storedSessionId);
  }, []);

  /* Load chat history */
  useEffect(() => {
    if (!sessionId) return;

    apiService
      .getChatHistory(sessionId)
      .then((history) => setMessages(Array.isArray(history) ? history : []))
      .catch(() => setMessages([]));
  }, [sessionId]);

  /* Load all sessions */
  const loadSessions = async () => {
    try {
      const data = await apiService.getChatSessions();
      setSessions(Array.isArray(data) ? data : []);
    } catch {
      setSessions([]);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  /* Auto scroll */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ===============================
     Send Message
  ================================ */
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading || !sessionId) return;

    const userText = inputMessage;
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInputMessage("");
    setLoading(true);

    try {
      const response = await apiService.sendChatMessage({
        message: userText,
        sessionId,
        businessType,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.content,
          locations: response.locations || [],
        },
      ]);

      if (response.locations && response.locations.length > 0) {
        onLocationsUpdate?.(response.locations);
      }

      await loadSessions();
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    const newId = crypto.randomUUID();
    localStorage.setItem("chat_session_id", newId);
    setSessionId(newId);
    setMessages([]);
  };

  const loadSession = async (id: string) => {
    localStorage.setItem("chat_session_id", id);
    setSessionId(id);
    try {
      const history = await apiService.getChatHistory(id);
      setMessages(Array.isArray(history) ? history : []);
    } catch {
      setMessages([]);
    }
  };

  const deleteSession = async (id: string) => {
    try {
      await apiService.deleteChatSession(id);
      if (sessionId === id) {
        startNewChat();
      } else {
        await loadSessions();
      }
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex h-full bg-white rounded-xl shadow-lg overflow-hidden">
      {/* History */}
      <div className="w-64 bg-gray-100 border-r p-3 flex flex-col">
        <button
          onClick={startNewChat}
          className="flex items-center justify-center gap-2 mb-3 bg-blue-600 text-white py-2 rounded-lg text-sm"
        >
          <Plus size={16} /> New Chat
        </button>

        <div className="text-xs font-semibold text-gray-600 mb-2">
          Chat History
        </div>

        <div className="flex-1 overflow-y-auto space-y-2">
          {sessions.map((s, i) => (
            <div
              key={s.sessionId}
              className={`flex items-center gap-2 w-full px-3 py-2 rounded text-sm hover:bg-gray-200 ${
                sessionId === s.sessionId ? "bg-gray-300" : ""
              }`}
            >
              <button
                onClick={() => loadSession(s.sessionId)}
                className="flex-1 text-left"
              >
                Conversation {i + 1}
              </button>
              <button
                onClick={() => deleteSession(s.sessionId)}
                className="text-gray-500 hover:text-red-600"
                title="Delete conversation"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 flex flex-col">
        <div className="bg-gradient-to-r from-blue-600 to-green-600 p-4 text-white">
          <div className="flex items-center space-x-3">
            <Bot className="w-7 h-7" />
            <div>
              <h2 className="text-lg font-bold">AI Business Assistant</h2>
              <p className="text-xs text-blue-100">
                Two-wheeler advisor for local areas
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          <div className="space-y-4">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[70%] px-4 py-3 rounded-xl ${
                    m.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border"
                  }`}
                >
                  {(m.content || "").split("\n").map((line: string, j: number) => (
                    <p key={j}>{line}</p>
                  ))}

                  {Array.isArray(m.locations) && m.locations.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {m.locations.map((loc: LocationData) => (
                        <div key={loc.id} className="flex items-center gap-2">
                          <button
                            onClick={() => onLocationSelect?.(loc)}
                            className="text-blue-600 hover:underline text-sm"
                          >
                            {loc.name}
                          </button>
                          {loc.mapUrl && (
                            <a
                              href={loc.mapUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-gray-500 hover:text-gray-700"
                            >
                              Open in Maps
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2">
                <Loader2 className="animate-spin w-4 h-4 text-blue-600" />
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        <form
          onSubmit={handleSendMessage}
          className="p-3 border-t flex gap-2"
        >
          <input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            className="flex-1 border rounded-lg px-3 py-2"
            placeholder="Ask about business locations..."
          />
          <button
            type="submit"
            disabled={loading || !sessionId}
            className="bg-blue-600 text-white px-4 rounded-lg"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
