import { useState } from "react";
import { sendChatMessage } from "../services/api";

export default function ChatWindow({ workspaceId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend() {
    const question = input.trim();
    if (!question || sending) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setSending(true);

    try {
      const { answer } = await sendChatMessage(workspaceId, question);
      setMessages((prev) => [...prev, { role: "assistant", text: answer }]);
    } catch (err) {
      const text = err.response?.data?.error || "Something went wrong.";
      setMessages((prev) => [...prev, { role: "assistant", text }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-message-${m.role}`}>
            {m.text}
          </div>
        ))}
        {sending && <div className="chat-message chat-message-assistant">Thinking...</div>}
      </div>
      <div className="chat-input">
        <input
          value={input}
          placeholder="Ask a question about your documents..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend} disabled={sending}>
          Send
        </button>
      </div>
    </div>
  );
}
