import { useState, useRef, useEffect } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import IconButton from "@mui/material/IconButton";
import Chip from "@mui/material/Chip";
import Avatar from "@mui/material/Avatar";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import SendIcon from "@mui/icons-material/Send";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";
import client from "../../api/client";
import CourseCard from "../courses/CourseCard";

const SUGGESTIONS = [
  "I want to learn machine learning",
  "What courses are good for beginners?",
  "Help me plan a career in data science",
  "Compare cloud computing courses",
];

const MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
];

export default function Explore() {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "Hello! I'm your Course Finder AI assistant. I can help you discover courses, explore career paths, and plan your learning journey. What would you like to explore today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    setInput("");
    setLoading(true);

    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      // Build history from past messages (exclude the just-added user message)
      const history = messages
        .filter((m) => m.role === "user" || m.role === "ai")
        .map((m) => ({
          role: m.role === "ai" ? "assistant" : "user",
          content: m.text,
        }));
      const res = await client.post("/chat", {
        message: msg,
        user_id: user.id || null,
        conversation_id: conversationId,
        history,
      });
      const data = res.data;
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: data.reply,
          toolCalls: data.tool_calls,
          latency: data.latency_ms,
          courses: data.courses || [],
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to get response. Please try again.";
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: detail },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: "flex", height: "calc(100vh - 48px)" }}>
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", bgcolor: "#fff" }}>
        {/* Model selector bar */}
        <Box
          sx={{
            px: 3,
            py: 1,
            borderBottom: "1px solid #eee",
            display: "flex",
            alignItems: "center",
            gap: 1.5,
          }}
        >
          <SmartToyIcon sx={{ color: "#6c63ff", fontSize: 18 }} />
          <Typography variant="body2" color="text.secondary" fontSize={13}>
            Model:
          </Typography>
          <Select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            size="small"
            sx={{ fontSize: 13, height: 32, minWidth: 140 }}
          >
            {MODELS.map((m) => (
              <MenuItem key={m.value} value={m.value} sx={{ fontSize: 13 }}>
                {m.label}
              </MenuItem>
            ))}
          </Select>
        </Box>

        {/* Messages */}
        <Box sx={{ flex: 1, overflow: "auto", p: 4 }}>
          {messages.map((msg, i) => (
            <Box
              key={i}
              sx={{
                display: "flex",
                gap: 1.5,
                mb: 2.5,
                flexDirection: msg.role === "user" ? "row-reverse" : "row",
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: msg.role === "ai" ? "#ede7f6" : "#e3f2fd",
                  color: msg.role === "ai" ? "#6c63ff" : "#1976d2",
                }}
              >
                {msg.role === "ai" ? <SmartToyIcon sx={{ fontSize: 16 }} /> : <PersonIcon sx={{ fontSize: 16 }} />}
              </Avatar>
              <Box sx={{ maxWidth: msg.courses?.length > 0 ? "85%" : "70%" }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 3,
                    bgcolor: msg.role === "ai" ? "#f5f5f5" : "#6c63ff",
                    color: msg.role === "user" ? "#fff" : "inherit",
                    borderTopLeftRadius: msg.role === "ai" ? 4 : undefined,
                    borderTopRightRadius: msg.role === "user" ? 4 : undefined,
                    fontSize: 14,
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {msg.text}
                  {msg.toolCalls?.length > 0 && (
                    <Box sx={{ mt: 1, display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                      {msg.toolCalls.map((t, j) => (
                        <Chip key={j} label={t} size="small" sx={{ fontSize: 11, height: 20, bgcolor: "#e8eaf6", color: "#3949ab" }} />
                      ))}
                      {msg.latency > 0 && (
                        <Chip label={`${(msg.latency / 1000).toFixed(1)}s`} size="small" sx={{ fontSize: 11, height: 20, bgcolor: "#e0f2f1", color: "#00695c" }} />
                      )}
                    </Box>
                  )}
                </Box>
                {msg.courses?.length > 0 && (
                  <Box
                    sx={{
                      mt: 1.5,
                      display: "grid",
                      gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", md: "1fr 1fr 1fr" },
                      gap: 1.5,
                    }}
                  >
                    {msg.courses.map((course) => (
                      <CourseCard key={course.id || course.title} course={course} />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          ))}
          {loading && (
            <Box sx={{ display: "flex", gap: 1.5, mb: 2.5 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: "#ede7f6", color: "#6c63ff" }}>
                <SmartToyIcon sx={{ fontSize: 16 }} />
              </Avatar>
              <Box sx={{ p: 2, borderRadius: 3, bgcolor: "#f5f5f5", borderTopLeftRadius: 4 }}>
                <CircularProgress size={18} sx={{ color: "#6c63ff" }} />
              </Box>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>

        {/* Suggestions */}
        <Box sx={{ px: 3, pb: 1, display: "flex", gap: 1, flexWrap: "wrap" }}>
          {SUGGESTIONS.map((s) => (
            <Chip
              key={s}
              label={s}
              size="small"
              variant="outlined"
              onClick={() => handleSend(s)}
              sx={{
                color: "#6c63ff",
                borderColor: "#d1c4e9",
                bgcolor: "#f5f3ff",
                fontSize: 12,
                "&:hover": { bgcolor: "#ede7f6" },
              }}
            />
          ))}
        </Box>

        {/* Input */}
        <Box sx={{ p: 2, px: 3, borderTop: "1px solid #eee", display: "flex", gap: 1, alignItems: "center" }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Ask me anything about courses..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <IconButton
            onClick={() => handleSend()}
            sx={{
              bgcolor: "#6c63ff",
              color: "#fff",
              width: 40,
              height: 40,
              "&:hover": { bgcolor: "#5a52d5" },
            }}
          >
            <SendIcon sx={{ fontSize: 18 }} />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}
