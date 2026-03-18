const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Yuichi Yamazaki";
pres.title = "Intelligent University Course Finder";

// ── Color Palette ──
const C = {
  bg: "0F1B2D",        // dark navy background
  bgLight: "F8FAFC",   // light slide bg
  bar: "0EA5E9",       // sky blue accent bar
  barDark: "0284C7",   // deeper sky blue
  title: "0F172A",     // near-black for titles on light bg
  titleLight: "F1F5F9",// light title on dark bg
  text: "334155",      // slate for body text
  textLight: "CBD5E1", // light text on dark bg
  muted: "64748B",     // muted text
  accent: "0EA5E9",    // sky blue
  accent2: "818CF8",   // indigo
  accent3: "22D3EE",   // cyan
  warn: "F59E0B",      // amber
  card: "FFFFFF",      // card bg
  cardBorder: "E2E8F0",// card border
  green: "10B981",     // emerald
  red: "EF4444",       // red
};

// ── Helpers ──
const leftBar = (slide, color) => {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: 5.625, fill: { color: color || C.bar },
  });
};

const slideTitle = (slide, text, opts = {}) => {
  slide.addText(text, {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: opts.size || 30, fontFace: "Calibri", bold: true,
    color: opts.color || C.title, margin: 0,
  });
};

const slideSubtitle = (slide, text, opts = {}) => {
  slide.addText(text, {
    x: 0.5, y: opts.y || 0.85, w: 9, h: 0.35,
    fontSize: 16, fontFace: "Calibri", color: C.muted, margin: 0,
  });
};

const sectionLabel = (slide, text, x, y) => {
  slide.addText(text.toUpperCase(), {
    x: x || 0.5, y: y || 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.bar,
    charSpacing: 2, margin: 0,
  });
};

const makeShadow = () => ({
  type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.1,
});

const addCard = (slide, x, y, w, h, opts = {}) => {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: opts.fill || C.card },
    shadow: makeShadow(),
    line: { color: C.cardBorder, width: 0.5 },
  });
  if (opts.accentColor) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h,
      fill: { color: opts.accentColor },
    });
  }
};

const addImageSafe = (slide, imgPath, opts) => {
  const absPath = path.resolve(imgPath);
  if (fs.existsSync(absPath)) {
    const data = fs.readFileSync(absPath);
    const ext = path.extname(absPath).toLowerCase().replace(".", "");
    const mime = ext === "png" ? "image/png" : "image/jpeg";
    const b64 = `${mime};base64,${data.toString("base64")}`;
    slide.addImage({ data: b64, ...opts });
    return true;
  }
  // Placeholder rectangle
  slide.addShape(pres.shapes.RECTANGLE, {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    fill: { color: "F1F5F9" }, line: { color: "334155", width: 1 },
  });
  slide.addText("[Image placeholder]", {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    fontSize: 12, color: "64748B", align: "center", valign: "middle",
  });
  return false;
};

// ══════════════════════════════════════════════════════════
// SLIDE 1 — Title
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);

  s.addText("Intelligent University\nCourse Finder", {
    x: 0.5, y: 1.2, w: 9, h: 1.8,
    fontSize: 44, fontFace: "Calibri", bold: true, color: C.bar,
    lineSpacingMultiple: 1.1, margin: 0,
  });
  s.addText("AI-Powered Multimodal Course Discovery System", {
    x: 0.5, y: 3.1, w: 9, h: 0.5,
    fontSize: 20, fontFace: "Calibri", color: C.text, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.7, w: 2.5, h: 0.04, fill: { color: C.bar },
  });
  s.addText("Yuichi Yamazaki  |  FDE Capstone  |  March 2026", {
    x: 0.5, y: 4.0, w: 9, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.muted, margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 2 — Market & Intro
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "MARKET OPPORTUNITY");
  slideTitle(s, "Online Education is a Growing Market", { y: 0.55 });

  // Big stat
  s.addText("$279B", {
    x: 0.5, y: 1.3, w: 3, h: 1.2,
    fontSize: 60, fontFace: "Calibri", bold: true, color: C.bar, margin: 0,
  });
  s.addText("Global e-learning market by 2029", {
    x: 0.5, y: 2.4, w: 3.5, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.muted, margin: 0,
  });

  // Problem statement card
  addCard(s, 4.2, 1.3, 5.3, 1.8, { accentColor: C.warn });
  s.addText("THE PROBLEM", {
    x: 4.5, y: 1.4, w: 4, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.warn, charSpacing: 2, margin: 0,
  });
  s.addText([
    { text: "Too many courses, not enough guidance.\n", options: { fontSize: 18, bold: true, color: C.title } },
    { text: "Students struggle to find the right learning path\namong thousands of options.", options: { fontSize: 14, color: C.text } },
  ], { x: 4.5, y: 1.75, w: 4.8, h: 1.2, margin: 0 });

  // Approach
  addCard(s, 0.5, 3.3, 9, 1.8, { accentColor: C.bar });
  s.addText("OUR APPROACH", {
    x: 0.8, y: 3.4, w: 4, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.bar, charSpacing: 2, margin: 0,
  });
  s.addText([
    { text: "Multi-Agent AI system ", options: { fontSize: 18, bold: true, color: C.title } },
    { text: "for course discovery, skill gap analysis, and learning path planning.\n", options: { fontSize: 16, color: C.text } },
    { text: "Built as PoC & PoB with production-grade architecture.", options: { fontSize: 14, color: C.muted } },
  ], { x: 0.8, y: 3.75, w: 8.5, h: 1.2, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 3 — Demo
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);

  s.addText("Live Demo", {
    x: 0.5, y: 1.8, w: 9, h: 1.2,
    fontSize: 52, fontFace: "Calibri", bold: true, color: C.bar,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.2, y: 3.2, w: 1.6, h: 0.04, fill: { color: C.bar },
  });
  s.addText("Intelligent Course Discovery in Action", {
    x: 1, y: 3.5, w: 8, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.muted, align: "center", margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 4a — System Architecture: Container View
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "SYSTEM ARCHITECTURE");
  slideTitle(s, "Docker Compose — Container View");

  // Container boxes
  const containers = [
    { name: "Frontend", tech: "React + Vite + MUI", port: ":5173", x: 0.5, color: C.accent },
    { name: "Gateway", tech: "FastAPI", port: ":8000", x: 2.6, color: C.barDark },
    { name: "Course Service", tech: "FastAPI", port: ":8001", x: 4.7, color: C.accent2 },
    { name: "User Service", tech: "FastAPI", port: ":8002", x: 4.7, color: C.accent2 },
    { name: "AI Service", tech: "FastAPI + Agents SDK", port: ":8003", x: 6.8, color: C.accent3 },
  ];

  // Frontend
  addCard(s, 0.5, 1.3, 1.8, 1.6, { accentColor: C.accent });
  s.addText("Frontend", { x: 0.7, y: 1.4, w: 1.5, h: 0.35, fontSize: 14, bold: true, color: C.title, margin: 0 });
  s.addText("React + Vite + MUI\n:5173", { x: 0.7, y: 1.75, w: 1.5, h: 0.8, fontSize: 11, color: C.muted, margin: 0 });

  // Arrow
  s.addText("→", { x: 2.3, y: 1.8, w: 0.3, h: 0.4, fontSize: 20, color: C.muted, align: "center" });

  // Gateway
  addCard(s, 2.7, 1.3, 1.8, 1.6, { accentColor: C.barDark });
  s.addText("Gateway", { x: 2.9, y: 1.4, w: 1.5, h: 0.35, fontSize: 14, bold: true, color: C.title, margin: 0 });
  s.addText("FastAPI\n:8000\nVite Proxy /api", { x: 2.9, y: 1.75, w: 1.5, h: 0.9, fontSize: 11, color: C.muted, margin: 0 });

  // Arrows to services
  s.addText("→", { x: 4.5, y: 1.4, w: 0.3, h: 0.4, fontSize: 20, color: C.muted, align: "center" });
  s.addText("→", { x: 4.5, y: 2.1, w: 0.3, h: 0.4, fontSize: 20, color: C.muted, align: "center" });

  // Course Service
  addCard(s, 4.9, 1.15, 1.8, 0.7, { accentColor: C.accent2 });
  s.addText("Course Service", { x: 5.1, y: 1.2, w: 1.5, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText(":8001", { x: 5.1, y: 1.45, w: 1.5, h: 0.25, fontSize: 10, color: C.muted, margin: 0 });

  // User Service
  addCard(s, 4.9, 2.0, 1.8, 0.7, { accentColor: C.accent2 });
  s.addText("User Service", { x: 5.1, y: 2.05, w: 1.5, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText(":8002", { x: 5.1, y: 2.3, w: 1.5, h: 0.25, fontSize: 10, color: C.muted, margin: 0 });

  // Arrow to AI service
  s.addText("→", { x: 4.5, y: 3.0, w: 0.3, h: 0.4, fontSize: 20, color: C.muted, align: "center" });

  // AI Service (bigger)
  addCard(s, 4.9, 2.9, 1.8, 1.0, { accentColor: C.accent3 });
  s.addText("AI Service", { x: 5.1, y: 2.95, w: 1.5, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText("Agents SDK\n:8003", { x: 5.1, y: 3.2, w: 1.5, h: 0.5, fontSize: 10, color: C.muted, margin: 0 });

  // Data layer
  // MongoDB
  addCard(s, 7.2, 1.3, 1.5, 0.9, { accentColor: C.green });
  s.addText("MongoDB", { x: 7.4, y: 1.35, w: 1.2, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText("Document DB\n:27017", { x: 7.4, y: 1.6, w: 1.2, h: 0.45, fontSize: 10, color: C.muted, margin: 0 });

  // Qdrant
  addCard(s, 7.2, 2.4, 1.5, 0.9, { accentColor: C.accent3 });
  s.addText("Qdrant", { x: 7.4, y: 2.45, w: 1.2, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText("Vector DB\n:6333", { x: 7.4, y: 2.7, w: 1.2, h: 0.45, fontSize: 10, color: C.muted, margin: 0 });

  // Arrows to DBs
  s.addText("→", { x: 6.7, y: 1.5, w: 0.4, h: 0.3, fontSize: 16, color: C.muted, align: "center" });
  s.addText("→", { x: 6.7, y: 2.6, w: 0.4, h: 0.3, fontSize: 16, color: C.muted, align: "center" });

  // External
  addCard(s, 7.2, 3.5, 1.5, 0.7, { accentColor: C.warn });
  s.addText("OpenAI API", { x: 7.4, y: 3.55, w: 1.2, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText("LLM + Embedding", { x: 7.4, y: 3.8, w: 1.2, h: 0.25, fontSize: 10, color: C.muted, margin: 0 });

  // LangFuse
  addCard(s, 0.5, 4.3, 2.5, 0.8, { accentColor: C.warn });
  s.addText("LangFuse", { x: 0.7, y: 4.35, w: 2, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0 });
  s.addText("Observability & Tracing", { x: 0.7, y: 4.6, w: 2, h: 0.25, fontSize: 10, color: C.muted, margin: 0 });

  // Docker compose boundary
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.05, w: 9.15, h: 3.8,
    fill: { color: "FFFFFF", transparency: 100 },
    line: { color: C.bar, width: 1.5, dashType: "dash" },
  });
  s.addText("Docker Compose", {
    x: 0.5, y: 4.65, w: 2, h: 0.3, fontSize: 11, color: C.bar, italic: true, margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 4b — System Architecture: Endpoint View
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "SYSTEM ARCHITECTURE");
  slideTitle(s, "API Endpoint Map");

  // Gateway endpoints
  addCard(s, 0.5, 1.3, 4.2, 3.8, { accentColor: C.barDark });
  s.addText("Gateway :8000", { x: 0.7, y: 1.4, w: 3.5, h: 0.35, fontSize: 16, bold: true, color: C.title, margin: 0 });

  const gwEndpoints = [
    ["POST", "/api/chat", "AI chat (→ AI Service)"],
    ["POST", "/api/analyze", "Full analysis (→ AI Service)"],
    ["GET", "/api/courses", "Course search (→ Course)"],
    ["GET", "/api/courses/:id", "Course detail (→ Course)"],
    ["POST", "/api/users", "User CRUD (→ User)"],
    ["GET", "/api/users/:id/profile", "User profile (→ User)"],
    ["GET", "/health", "Health check"],
  ];

  gwEndpoints.forEach((ep, i) => {
    const yPos = 1.9 + i * 0.42;
    const methodColor = ep[0] === "POST" ? C.accent3 : C.green;
    s.addText(ep[0], { x: 0.75, y: yPos, w: 0.6, h: 0.3, fontSize: 10, bold: true, color: methodColor, margin: 0 });
    s.addText(ep[1], { x: 1.4, y: yPos, w: 1.8, h: 0.3, fontSize: 11, bold: true, color: C.title, fontFace: "Consolas", margin: 0 });
    s.addText(ep[2], { x: 3.3, y: yPos, w: 1.3, h: 0.3, fontSize: 9, color: C.muted, margin: 0 });
  });

  // AI Service endpoints
  addCard(s, 5.0, 1.3, 4.5, 2.3, { accentColor: C.accent3 });
  s.addText("AI Service :8003", { x: 5.2, y: 1.4, w: 3.5, h: 0.35, fontSize: 16, bold: true, color: C.title, margin: 0 });

  const aiEndpoints = [
    ["POST", "/chat", "Multi-agent conversation"],
    ["POST", "/analyze", "Run all 3 specialist agents"],
    ["POST", "/analyze/skill-gap", "Skill Gap Analyst only"],
    ["POST", "/analyze/career", "Career Advisor only"],
    ["POST", "/analyze/learning-path", "Learning Path only"],
  ];

  aiEndpoints.forEach((ep, i) => {
    const yPos = 1.9 + i * 0.3;
    s.addText(ep[0], { x: 5.25, y: yPos, w: 0.55, h: 0.25, fontSize: 10, bold: true, color: C.accent3, margin: 0 });
    s.addText(ep[1], { x: 5.85, y: yPos, w: 2, h: 0.25, fontSize: 11, bold: true, color: C.title, fontFace: "Consolas", margin: 0 });
    s.addText(ep[2], { x: 7.9, y: yPos, w: 1.5, h: 0.25, fontSize: 9, color: C.muted, margin: 0 });
  });

  // Course & User Service
  addCard(s, 5.0, 3.8, 2.1, 1.2, { accentColor: C.accent2 });
  s.addText("Course :8001", { x: 5.15, y: 3.85, w: 1.8, h: 0.25, fontSize: 13, bold: true, color: C.title, margin: 0 });
  s.addText("CRUD + text search\n+ filters", { x: 5.15, y: 4.15, w: 1.8, h: 0.6, fontSize: 10, color: C.muted, margin: 0 });

  addCard(s, 7.4, 3.8, 2.1, 1.2, { accentColor: C.accent2 });
  s.addText("User :8002", { x: 7.55, y: 3.85, w: 1.8, h: 0.25, fontSize: 13, bold: true, color: C.title, margin: 0 });
  s.addText("Profile CRUD\n+ preferences", { x: 7.55, y: 4.15, w: 1.8, h: 0.6, fontSize: 10, color: C.muted, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 5 — Agent Architecture Overview
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "AGENT ARCHITECTURE");
  slideTitle(s, "Multi-Agent System — AI Chat Flow");

  // Input guardrails
  addCard(s, 0.5, 1.3, 2.8, 0.8, { accentColor: C.red });
  s.addText("Input Guardrails", { x: 0.7, y: 1.35, w: 2.4, h: 0.3, fontSize: 13, bold: true, color: C.title, margin: 0 });
  s.addText("Sanitize • Injection Check • Topic • PII", { x: 0.7, y: 1.65, w: 2.4, h: 0.3, fontSize: 9, color: C.muted, margin: 0 });

  // Arrow down
  s.addText("↓", { x: 1.6, y: 2.1, w: 0.5, h: 0.3, fontSize: 18, color: C.muted, align: "center" });

  // Learning Advisor (central, big)
  addCard(s, 0.5, 2.4, 3.5, 1.5, { accentColor: C.bar });
  s.addText("Learning Advisor", { x: 0.7, y: 2.5, w: 3, h: 0.35, fontSize: 18, bold: true, color: C.bar, margin: 0 });
  s.addText("Router Agent — orchestrates all queries", { x: 0.7, y: 2.85, w: 3, h: 0.3, fontSize: 11, color: C.muted, margin: 0 });
  s.addText([
    { text: "Simple query → ", options: { fontSize: 11, bold: true, color: C.title } },
    { text: "retrieve_courses directly\n", options: { fontSize: 11, color: C.text } },
    { text: "Complex query → ", options: { fontSize: 11, bold: true, color: C.title, breakLine: true } },
    { text: "handoff to specialist", options: { fontSize: 11, color: C.text } },
  ], { x: 0.7, y: 3.2, w: 3, h: 0.6, margin: 0 });

  // Specialist agents
  const specialists = [
    { name: "Skill Gap\nAnalyst", color: C.accent, y: 1.3 },
    { name: "Career\nAdvisor", color: C.accent2, y: 2.5 },
    { name: "Learning Path\nDesigner", color: C.accent3, y: 3.7 },
  ];

  specialists.forEach((agent, i) => {
    addCard(s, 5.0, agent.y, 2.2, 1.0, { accentColor: agent.color });
    s.addText(agent.name, {
      x: 5.2, y: agent.y + 0.1, w: 1.9, h: 0.8,
      fontSize: 14, bold: true, color: C.title, margin: 0,
    });
    // Arrow from advisor to agent
    s.addText("handoff →", {
      x: 4.0, y: agent.y + 0.3, w: 1, h: 0.3,
      fontSize: 10, color: C.muted, align: "center", margin: 0,
    });
  });

  // Tools column
  addCard(s, 7.6, 1.3, 2, 3.4, { accentColor: C.warn });
  s.addText("Tools", { x: 7.8, y: 1.35, w: 1.7, h: 0.3, fontSize: 14, bold: true, color: C.title, margin: 0 });
  const tools = ["retrieve_courses", "web_search", "get_user_profile", "update_user_profile", "get_course_details"];
  tools.forEach((t, i) => {
    s.addText(t, {
      x: 7.8, y: 1.75 + i * 0.38, w: 1.7, h: 0.3,
      fontSize: 10, fontFace: "Consolas", color: C.text, margin: 0,
    });
  });
  s.addText("→", { x: 7.2, y: 2.8, w: 0.4, h: 0.3, fontSize: 16, color: C.muted, align: "center" });

  // Output guardrails
  addCard(s, 0.5, 4.3, 2.8, 0.8, { accentColor: C.red });
  s.addText("Output Guardrails", { x: 0.7, y: 4.35, w: 2.4, h: 0.3, fontSize: 13, bold: true, color: C.title, margin: 0 });
  s.addText("PII Redact • Stack Trace • Env Vars", { x: 0.7, y: 4.65, w: 2.4, h: 0.3, fontSize: 9, color: C.muted, margin: 0 });

  s.addText("↓", { x: 1.6, y: 3.95, w: 0.5, h: 0.3, fontSize: 18, color: C.muted, align: "center" });
}

// ══════════════════════════════════════════════════════════
// SLIDES 6-8 — Individual Agent Details
// ══════════════════════════════════════════════════════════
const agentDetails = [
  {
    name: "Skill Gap Analyst",
    color: C.accent,
    input: "User profile + Target role query",
    tools: ["get_user_profile", "web_search", "retrieve_courses"],
    toolDescs: ["Current skills", "Required skills 2025", "Gap-filling courses"],
    output: "gaps[], recommended_courses[],\npriority_ranking",
    example: '"I want to become an ML Engineer"',
  },
  {
    name: "Career Advisor",
    color: C.accent2,
    input: "User profile + Career interest query",
    tools: ["get_user_profile", "web_search", "retrieve_courses"],
    toolDescs: ["Current skills", "Market data / salary", "Aligned courses"],
    output: "career_paths[], salary_data,\nrecommended_courses[]",
    example: '"What career paths fit my data skills?"',
  },
  {
    name: "Learning Path Designer",
    color: C.accent3,
    input: "User profile + Learning goal query",
    tools: ["retrieve_courses", "get_course_details", "get_user_profile"],
    toolDescs: ["Candidate courses", "Prerequisites / modules", "Skill level"],
    output: "learning_path[],\n3-6 courses Beginner→Advanced",
    example: '"Create a 6-month plan for full-stack dev"',
  },
];

agentDetails.forEach((agent) => {
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "AGENT DETAIL");
  slideTitle(s, agent.name);

  // Example query
  s.addText(agent.example, {
    x: 0.5, y: 0.9, w: 9, h: 0.35,
    fontSize: 14, fontFace: "Consolas", italic: true, color: C.muted, margin: 0,
  });

  // Input card
  addCard(s, 0.5, 1.5, 2.5, 1.0, { accentColor: C.green });
  s.addText("INPUT", { x: 0.7, y: 1.55, w: 2, h: 0.25, fontSize: 11, bold: true, color: C.green, charSpacing: 2, margin: 0 });
  s.addText(agent.input, { x: 0.7, y: 1.85, w: 2.1, h: 0.55, fontSize: 12, color: C.text, margin: 0 });

  // Tools (center - 3 cards)
  agent.tools.forEach((tool, i) => {
    const xPos = 3.3 + i * 1.5;
    addCard(s, xPos, 1.5, 1.35, 1.0, { accentColor: C.warn });
    s.addText(tool, { x: xPos + 0.15, y: 1.55, w: 1.2, h: 0.3, fontSize: 9, fontFace: "Consolas", bold: true, color: C.title, margin: 0 });
    s.addText(agent.toolDescs[i], { x: xPos + 0.15, y: 1.85, w: 1.1, h: 0.5, fontSize: 10, color: C.muted, margin: 0 });
  });

  // Output card
  addCard(s, 7.8, 1.5, 1.8, 1.0, { accentColor: agent.color });
  s.addText("OUTPUT", { x: 8.0, y: 1.55, w: 1.5, h: 0.25, fontSize: 11, bold: true, color: agent.color, charSpacing: 2, margin: 0 });
  s.addText(agent.output, { x: 8.0, y: 1.85, w: 1.5, h: 0.55, fontSize: 10, fontFace: "Consolas", color: C.text, margin: 0 });

  // Flow arrows
  s.addText("→", { x: 3.0, y: 1.8, w: 0.3, h: 0.3, fontSize: 16, color: C.muted, align: "center" });
  s.addText("→", { x: 7.5, y: 1.8, w: 0.3, h: 0.3, fontSize: 16, color: C.muted, align: "center" });

  // Agent description area (bottom half)
  addCard(s, 0.5, 2.9, 9, 2.3, { accentColor: agent.color });
  s.addText("HOW IT WORKS", { x: 0.7, y: 3.0, w: 3, h: 0.25, fontSize: 11, bold: true, color: agent.color, charSpacing: 2, margin: 0 });
});

// ══════════════════════════════════════════════════════════
// SLIDE 9 — Retrieval Evolution
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "RETRIEVAL STRATEGY");
  slideTitle(s, "Evolution of Course Retrieval");

  // Phase 2
  addCard(s, 0.5, 1.3, 2.8, 2.5, { accentColor: C.muted });
  s.addText("Phase 2", { x: 0.7, y: 1.4, w: 2.4, h: 0.3, fontSize: 18, bold: true, color: C.muted, margin: 0 });
  s.addText("Keyword Only", { x: 0.7, y: 1.75, w: 2.4, h: 0.3, fontSize: 14, bold: true, color: C.title, margin: 0 });
  s.addText("MongoDB text search\n\nSimple but misses\nsemantic intent", {
    x: 0.7, y: 2.1, w: 2.4, h: 1.5, fontSize: 12, color: C.text, margin: 0,
  });

  // Arrow
  s.addText("→", { x: 3.3, y: 2.3, w: 0.5, h: 0.4, fontSize: 24, color: C.bar, align: "center", bold: true });

  // v2.0
  addCard(s, 3.8, 1.3, 2.6, 2.5, { accentColor: C.warn });
  s.addText("v2.0", { x: 4.0, y: 1.4, w: 2.2, h: 0.3, fontSize: 18, bold: true, color: C.warn, margin: 0 });
  s.addText("LLM Tool Selection", { x: 4.0, y: 1.75, w: 2.2, h: 0.3, fontSize: 14, bold: true, color: C.title, margin: 0 });
  s.addText("LLM chooses:\nkeyword OR semantic OR filter\n\nTool selection accuracy: 0.67\n1/3 queries → wrong tool", {
    x: 4.0, y: 2.1, w: 2.2, h: 1.5, fontSize: 11, color: C.text, margin: 0,
  });

  // Arrow
  s.addText("→", { x: 6.4, y: 2.3, w: 0.5, h: 0.4, fontSize: 24, color: C.bar, align: "center", bold: true });

  // v2.1 (current)
  addCard(s, 6.9, 1.3, 2.7, 2.5, { accentColor: C.green });
  s.addText("v2.1 (current)", { x: 7.1, y: 1.4, w: 2.3, h: 0.3, fontSize: 18, bold: true, color: C.green, margin: 0 });
  s.addText("Hybrid Search", { x: 7.1, y: 1.75, w: 2.3, h: 0.3, fontSize: 14, bold: true, color: C.title, margin: 0 });
  s.addText("BM25 + Dense + RRF\nAlways run both → merge\n\nNo LLM tool selection\n→ deterministic, faster", {
    x: 7.1, y: 2.1, w: 2.3, h: 1.5, fontSize: 11, color: C.text, margin: 0,
  });

  // Key insight box
  addCard(s, 0.5, 4.2, 9, 1.0, { accentColor: C.bar });
  s.addText([
    { text: "Key Insight: ", options: { fontSize: 16, bold: true, color: C.bar } },
    { text: "Keyword vs. semantic is not an LLM judgment call — run both and merge.", options: { fontSize: 16, color: C.title } },
  ], { x: 0.7, y: 4.35, w: 8.5, h: 0.6, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 10 — Data: Domain Distribution
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);
  s.addText("DATA ANALYSIS", {
    x: 0.5, y: 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent3, charSpacing: 2, margin: 0,
  });
  s.addText("6,645 Courses — Domain Distribution", {
    x: 0.5, y: 0.55, w: 9, h: 0.5,
    fontSize: 26, bold: true, color: C.title, margin: 0,
  });

  addImageSafe(s, "charts/domain_distribution.png", {
    x: 0.3, y: 1.2, w: 9.4, h: 4.2,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 11 — Data: Level Distribution
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);
  s.addText("DATA ANALYSIS", {
    x: 0.5, y: 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent3, charSpacing: 2, margin: 0,
  });
  s.addText("54% Beginner — Consistent Across All Domains", {
    x: 0.5, y: 0.55, w: 9, h: 0.5,
    fontSize: 26, bold: true, color: C.title, margin: 0,
  });

  // Level pie on left
  addImageSafe(s, "charts/level_distribution.png", {
    x: 0.3, y: 1.2, w: 4.5, h: 3.0,
  });
  // Level by domain on right
  addImageSafe(s, "charts/level_by_domain.png", {
    x: 4.8, y: 1.2, w: 5, h: 3.0,
  });

  // Insight box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.4, w: 9, h: 0.8,
    fill: { color: "F1F5F9" },
  });
  s.addText([
    { text: "Insight: ", options: { fontSize: 14, bold: true, color: C.accent3 } },
    { text: "Beginner-heavy distribution is consistent across domains. Agents must filter by level to surface Advanced content.", options: { fontSize: 13, color: C.text } },
  ], { x: 0.7, y: 4.5, w: 8.5, h: 0.6, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 12 — Embedding: Topic (clear clusters)
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);
  s.addText("EMBEDDING ANALYSIS", {
    x: 0.5, y: 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent3, charSpacing: 2, margin: 0,
  });
  s.addText("Topic → Clear Clusters in Embedding Space", {
    x: 0.5, y: 0.55, w: 9, h: 0.5,
    fontSize: 26, bold: true, color: C.title, margin: 0,
  });

  // Placeholder for t-SNE topic screenshot
  addImageSafe(s, "charts/tsne_topic.png", {
    x: 0.3, y: 1.15, w: 6, h: 3.8,
  });

  // Explanation
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.5, y: 1.15, w: 3.2, h: 3.8, fill: { color: "F1F5F9" },
  });
  s.addText([
    { text: "Embedding input:\n", options: { fontSize: 13, bold: true, color: C.accent3, breakLine: true } },
    { text: "title + description only\n\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Result:\n", options: { fontSize: 13, bold: true, color: C.accent3, breakLine: true } },
    { text: "Topic/subject clearly captured\nby semantic similarity.\n\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Business vs. Tech domains\nseparate cleanly.", options: { fontSize: 12, color: C.text } },
  ], { x: 6.7, y: 1.3, w: 2.8, h: 3.5, margin: 0, valign: "top" });
}

// ══════════════════════════════════════════════════════════
// SLIDE 13 — Embedding: Level/Org/Skill (no clusters)
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);
  s.addText("EMBEDDING ANALYSIS", {
    x: 0.5, y: 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent3, charSpacing: 2, margin: 0,
  });
  s.addText("Level / Organization / Skill → No Clusters", {
    x: 0.5, y: 0.55, w: 9, h: 0.5,
    fontSize: 26, bold: true, color: C.title, margin: 0,
  });

  // 3 placeholder images side by side
  addImageSafe(s, "charts/tsne_level.png", {
    x: 0.3, y: 1.2, w: 3, h: 2.2,
  });
  s.addText("Level", { x: 0.3, y: 3.4, w: 3, h: 0.25, fontSize: 11, color: C.muted, align: "center", margin: 0 });

  addImageSafe(s, "charts/tsne_organization.png", {
    x: 3.5, y: 1.2, w: 3, h: 2.2,
  });
  s.addText("Organization", { x: 3.5, y: 3.4, w: 3, h: 0.25, fontSize: 11, color: C.muted, align: "center", margin: 0 });

  addImageSafe(s, "charts/tsne_skill.png", {
    x: 6.7, y: 1.2, w: 3, h: 2.2,
  });
  s.addText("Skill", { x: 6.7, y: 3.4, w: 3, h: 0.25, fontSize: 11, color: C.muted, align: "center", margin: 0 });

  // Explanation box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.8, w: 9, h: 1.5, fill: { color: "F1F5F9" },
  });
  s.addText([
    { text: "Why? ", options: { fontSize: 14, bold: true, color: C.warn } },
    { text: "Embedding uses title + description only. Level, organization, and granular skills are ", options: { fontSize: 13, color: C.text } },
    { text: "not encoded", options: { fontSize: 13, bold: true, color: C.warn } },
    { text: " in the embedding space.\n", options: { fontSize: 13, color: C.text } },
    { text: "→ These dimensions require payload filters and keyword (BM25) matching.", options: { fontSize: 13, color: C.accent3, breakLine: true } },
  ], { x: 0.7, y: 3.95, w: 8.5, h: 1.2, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 14 — Design Decision: Hybrid Search Rationale
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "DESIGN DECISION");
  slideTitle(s, "Data Analysis → Hybrid Search Design");

  // Table-like layout
  const rows = [
    { dim: "Topic / Subject", captured: "✓ Yes", evidence: "Clear t-SNE clusters", handling: "Dense vector\n(semantic search)", capturedColor: C.green },
    { dim: "Specific Skills", captured: "△ Partial", evidence: "Sparse data (29.4% missing)", handling: "BM25 keyword\nmatching", capturedColor: C.warn },
    { dim: "Difficulty Level", captured: "✗ No", evidence: "Uniform distribution", handling: "Qdrant\npayload filter", capturedColor: C.red },
    { dim: "Organization", captured: "✗ No", evidence: "Scattered across space", handling: "Qdrant\npayload filter", capturedColor: C.red },
    { dim: "Rating", captured: "✗ No", evidence: "Numeric metadata", handling: "Qdrant\npayload filter", capturedColor: C.red },
  ];

  // Headers
  const headerY = 1.15;
  s.addText("Dimension", { x: 0.5, y: headerY, w: 1.8, h: 0.35, fontSize: 12, bold: true, color: C.bar, margin: 0 });
  s.addText("Captured?", { x: 2.4, y: headerY, w: 1.2, h: 0.35, fontSize: 12, bold: true, color: C.bar, margin: 0 });
  s.addText("Evidence", { x: 3.7, y: headerY, w: 2.5, h: 0.35, fontSize: 12, bold: true, color: C.bar, margin: 0 });
  s.addText("RAG Handling", { x: 6.5, y: headerY, w: 3, h: 0.35, fontSize: 12, bold: true, color: C.bar, margin: 0 });

  s.addShape(pres.shapes.LINE, {
    x: 0.5, y: 1.5, w: 9, h: 0,
    line: { color: C.cardBorder, width: 1 },
  });

  rows.forEach((row, i) => {
    const yPos = 1.6 + i * 0.7;

    // Alternate row bg
    if (i % 2 === 0) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.5, y: yPos, w: 9, h: 0.65,
        fill: { color: "F1F5F9" },
      });
    }

    s.addText(row.dim, { x: 0.6, y: yPos + 0.1, w: 1.7, h: 0.4, fontSize: 13, bold: true, color: C.title, margin: 0 });
    s.addText(row.captured, { x: 2.5, y: yPos + 0.1, w: 1, h: 0.4, fontSize: 13, bold: true, color: row.capturedColor, margin: 0 });
    s.addText(row.evidence, { x: 3.8, y: yPos + 0.1, w: 2.4, h: 0.4, fontSize: 11, color: C.text, margin: 0 });
    s.addText(row.handling, { x: 6.6, y: yPos + 0.05, w: 2.8, h: 0.55, fontSize: 11, bold: true, color: C.title, margin: 0 });
  });

  // Bottom insight
  addCard(s, 0.5, 4.3, 9, 0.9, { accentColor: C.bar });
  s.addText([
    { text: "Conclusion: ", options: { fontSize: 14, bold: true, color: C.bar } },
    { text: "Embedding captures WHAT the course is about. Metadata (level, org, rating) needs structural filtering.", options: { fontSize: 13, color: C.title } },
  ], { x: 0.7, y: 4.45, w: 8.5, h: 0.5, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 15 — RAG Architecture: Indexing
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "RAG ARCHITECTURE");
  slideTitle(s, "Indexing Pipeline — Data Ingestion");

  // Flow: CSV → MongoDB → Embedding → Qdrant
  const steps = [
    { label: "CSV\n6,645 courses", x: 0.5, color: C.muted },
    { label: "MongoDB\nDocument store", x: 2.6, color: C.green },
    { label: "OpenAI\ntext-embedding\n-3-small", x: 4.7, color: C.warn },
    { label: "Qdrant\nDense + BM25\nvectors", x: 6.8, color: C.accent3 },
  ];

  steps.forEach((step, i) => {
    addCard(s, step.x, 1.5, 1.9, 1.4, { accentColor: step.color });
    s.addText(step.label, {
      x: step.x + 0.15, y: 1.6, w: 1.7, h: 1.2,
      fontSize: 13, bold: true, color: C.title, align: "center", valign: "middle", margin: 0,
    });
    if (i < steps.length - 1) {
      s.addText("→", {
        x: step.x + 1.9, y: 1.9, w: 0.7, h: 0.4,
        fontSize: 24, color: C.bar, align: "center", bold: true,
      });
    }
  });

  // Details below
  addCard(s, 0.5, 3.3, 4.2, 1.8, { accentColor: C.accent3 });
  s.addText("Dense Vector (Semantic)", { x: 0.7, y: 3.4, w: 3.8, h: 0.3, fontSize: 14, bold: true, color: C.accent3, margin: 0 });
  s.addText([
    { text: "Input: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "title + description\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Model: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "text-embedding-3-small\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Dimensions: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "1,536", options: { fontSize: 12, color: C.text } },
  ], { x: 0.7, y: 3.8, w: 3.8, h: 1.1, margin: 0 });

  addCard(s, 5.0, 3.3, 4.5, 1.8, { accentColor: C.warn });
  s.addText("BM25 Sparse Vector (Keyword)", { x: 5.2, y: 3.4, w: 4, h: 0.3, fontSize: 14, bold: true, color: C.warn, margin: 0 });
  s.addText([
    { text: "Input: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "title + description + skills\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Model: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "Qdrant/bm25 (built-in)\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Purpose: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "Exact skill/tool name matching", options: { fontSize: 12, color: C.text } },
  ], { x: 5.2, y: 3.8, w: 4, h: 1.1, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 16 — RAG Architecture: Query
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "RAG ARCHITECTURE");
  slideTitle(s, "Query Pipeline — Hybrid Search + RRF");

  // Query flow
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 1.8, h: 0.6,
    fill: { color: C.bar },
  });
  s.addText("User Query", {
    x: 0.5, y: 1.3, w: 1.8, h: 0.6,
    fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0,
  });

  // Arrow to embedding
  s.addText("→", { x: 2.3, y: 1.35, w: 0.4, h: 0.5, fontSize: 20, color: C.bar, align: "center" });

  // Embedding
  s.addShape(pres.shapes.RECTANGLE, {
    x: 2.7, y: 1.3, w: 2, h: 0.6,
    fill: { color: C.warn },
  });
  s.addText("Embed (1536-dim)", {
    x: 2.7, y: 1.3, w: 2, h: 0.6,
    fontSize: 12, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0,
  });

  // Split into two paths
  // BM25 path (top)
  addCard(s, 5.2, 1.1, 2.2, 0.6, { accentColor: C.warn });
  s.addText("BM25 Search", {
    x: 5.4, y: 1.15, w: 1.9, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0,
  });
  s.addText("weight: 1.0  |  limit: 20", {
    x: 5.4, y: 1.4, w: 1.9, h: 0.2, fontSize: 9, color: C.muted, margin: 0,
  });

  // Dense path (bottom)
  addCard(s, 5.2, 1.85, 2.2, 0.6, { accentColor: C.accent3 });
  s.addText("Dense Search", {
    x: 5.4, y: 1.9, w: 1.9, h: 0.25, fontSize: 12, bold: true, color: C.title, margin: 0,
  });
  s.addText("weight: 1.5  |  limit: 20", {
    x: 5.4, y: 2.15, w: 1.9, h: 0.2, fontSize: 9, color: C.muted, margin: 0,
  });

  // Arrows
  s.addText("→", { x: 4.7, y: 1.15, w: 0.5, h: 0.5, fontSize: 16, color: C.muted, align: "center" });
  s.addText("→", { x: 4.7, y: 1.9, w: 0.5, h: 0.5, fontSize: 16, color: C.muted, align: "center" });

  // RRF merge
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.8, y: 1.3, w: 1.8, h: 1.15,
    fill: { color: C.green },
  });
  s.addText("RRF\nFusion", {
    x: 7.8, y: 1.3, w: 1.8, h: 1.15,
    fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0,
  });

  s.addText("→", { x: 7.4, y: 1.15, w: 0.4, h: 0.5, fontSize: 16, color: C.muted, align: "center" });
  s.addText("→", { x: 7.4, y: 1.9, w: 0.4, h: 0.5, fontSize: 16, color: C.muted, align: "center" });

  // Payload filters
  addCard(s, 0.5, 2.7, 9, 1.0, { accentColor: C.accent2 });
  s.addText("Payload Filters (applied to both searches)", {
    x: 0.7, y: 2.8, w: 8.5, h: 0.3, fontSize: 14, bold: true, color: C.accent2, margin: 0,
  });
  s.addText([
    { text: "level ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: '(Beginner/Intermediate/Advanced)    ', options: { fontSize: 12, color: C.text } },
    { text: "min_rating ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "(≥ value)    ", options: { fontSize: 12, color: C.text } },
    { text: "organization ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "(text match)", options: { fontSize: 12, color: C.text } },
  ], { x: 0.7, y: 3.15, w: 8.5, h: 0.4, margin: 0 });

  // Why Qdrant box
  addCard(s, 0.5, 4.0, 9, 1.2, { accentColor: C.accent3 });
  s.addText("Why Qdrant?", { x: 0.7, y: 4.1, w: 2, h: 0.3, fontSize: 14, bold: true, color: C.accent3, margin: 0 });
  s.addText([
    { text: "Native Hybrid Search: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "BM25 + Dense + RRF in single API call\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Payload Filters: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "Structured metadata filtering on vector results\n", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "Docker Native: ", options: { fontSize: 12, bold: true, color: C.title } },
    { text: "Lightweight, fits Docker Compose stack", options: { fontSize: 12, color: C.text } },
  ], { x: 0.7, y: 4.4, w: 8.5, h: 0.7, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 17 — Web Search Architecture
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s);
  sectionLabel(s, "WEB SEARCH TOOL");
  slideTitle(s, "Real-Time Market Data via Web Search");

  // Flow
  const wsSteps = [
    { label: "Specialist Agent\n(Skill Gap / Career)", x: 0.5, w: 2.2, color: C.accent2 },
    { label: "web_search\ntool", x: 3.2, w: 1.5, color: C.warn },
    { label: "OpenAI\nResponses API\n+ web_search_preview", x: 5.2, w: 2.2, color: C.bar },
    { label: "Summarized\nMarket Data", x: 7.9, w: 1.7, color: C.green },
  ];

  wsSteps.forEach((step, i) => {
    addCard(s, step.x, 1.5, step.w, 1.2, { accentColor: step.color });
    s.addText(step.label, {
      x: step.x + 0.1, y: 1.6, w: step.w - 0.2, h: 1.0,
      fontSize: 12, bold: true, color: C.title, align: "center", valign: "middle", margin: 0,
    });
    if (i < wsSteps.length - 1) {
      s.addText("→", {
        x: step.x + step.w, y: 1.85, w: 0.5, h: 0.3,
        fontSize: 18, color: C.bar, align: "center", bold: true,
      });
    }
  });

  // Why web search matters
  addCard(s, 0.5, 3.1, 9, 2.0, { accentColor: C.bar });
  s.addText("Why Web Search Matters for Agents", {
    x: 0.7, y: 3.2, w: 8.5, h: 0.35, fontSize: 16, bold: true, color: C.bar, margin: 0,
  });

  // Two columns
  s.addText([
    { text: "Skill Gap Analyst\n", options: { fontSize: 13, bold: true, color: C.accent } },
    { text: "Searches for current required skills\nfor target roles (e.g., \"ML Engineer\nrequired skills 2025\")\n\n", options: { fontSize: 11, color: C.text } },
    { text: "Model: ", options: { fontSize: 11, bold: true, color: C.title } },
    { text: "gpt-4o-mini", options: { fontSize: 11, color: C.text } },
  ], { x: 0.7, y: 3.65, w: 4, h: 1.3, margin: 0 });

  s.addText([
    { text: "Career Advisor\n", options: { fontSize: 13, bold: true, color: C.accent2 } },
    { text: "Searches for salary data, job market\ntrends, career path information\nfor informed recommendations\n\n", options: { fontSize: 11, color: C.text } },
    { text: "Retry: ", options: { fontSize: 11, bold: true, color: C.title } },
    { text: "max 2 attempts, exponential backoff", options: { fontSize: 11, color: C.text } },
  ], { x: 5.0, y: 3.65, w: 4.3, h: 1.3, margin: 0 });
}

// ══════════════════════════════════════════════════════════
// SLIDE 18 — Appendix: Level x Domain detail
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  leftBar(s, C.bar);
  s.addText("APPENDIX", {
    x: 0.5, y: 0.25, w: 3, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent3, charSpacing: 2, margin: 0,
  });
  s.addText("Level Distribution by Domain (Detail)", {
    x: 0.5, y: 0.55, w: 9, h: 0.5,
    fontSize: 26, bold: true, color: C.title, margin: 0,
  });

  addImageSafe(s, "charts/level_by_domain.png", {
    x: 0.5, y: 1.2, w: 9, h: 4.0,
  });
}

// ══════════════════════════════════════════════════════════
// SAVE
// ══════════════════════════════════════════════════════════
const outPath = "/app/capstone_presentation.pptx";
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("Presentation saved to: " + outPath);
}).catch((err) => {
  console.error("Error:", err);
});
