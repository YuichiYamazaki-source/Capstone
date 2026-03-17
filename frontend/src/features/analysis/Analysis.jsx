import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Alert from "@mui/material/Alert";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import WorkIcon from "@mui/icons-material/Work";
import SchoolIcon from "@mui/icons-material/School";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import { useAuth } from "../../contexts/AuthContext";
import { getCourses } from "../courses/api";
import { RECOMMENDED_PATHS } from "../../constants/recommendedPaths";

const SKILL_DOMAINS = [
  { domain: "Data & Analytics", skills: ["python", "data analysis", "sql", "statistics", "data visualization"] },
  { domain: "AI & Machine Learning", skills: ["machine learning", "deep learning", "ai", "neural networks", "tensorflow"] },
  { domain: "Cloud & Infrastructure", skills: ["cloud computing", "aws", "google cloud", "devops", "docker"] },
  { domain: "Security", skills: ["cybersecurity", "network security", "encryption"] },
  { domain: "Business & Management", skills: ["project management", "leadership", "communication", "marketing"] },
  { domain: "Web Development", skills: ["javascript", "react", "html", "css", "node.js"] },
];

const CAREER_PATHS = [
  { title: "Data Scientist", requiredDomains: ["Data & Analytics", "AI & Machine Learning"], icon: <TrendingUpIcon /> },
  { title: "Cloud Engineer", requiredDomains: ["Cloud & Infrastructure", "Security"], icon: <SchoolIcon /> },
  { title: "Product Manager", requiredDomains: ["Business & Management", "Data & Analytics"], icon: <WorkIcon /> },
  { title: "ML Engineer", requiredDomains: ["AI & Machine Learning", "Cloud & Infrastructure", "Data & Analytics"], icon: <TrendingUpIcon /> },
];

export default function Analysis() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const profile = user?.profile;
  const [allCourses, setAllCourses] = useState([]);

  useEffect(() => {
    if (!user) { navigate("/login"); return; }
    getCourses({ limit: 100 }).then((d) => setAllCourses(d.courses)).catch(() => {});
  }, [user]);

  if (!profile?.skills?.length) {
    return (
      <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 4 }}>
        <Typography variant="h5" fontWeight={700} mb={2}>Personal Analysis</Typography>
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <Typography variant="body1" mb={2}>Complete your profile to see personalized analysis.</Typography>
          <Button variant="contained" onClick={() => navigate("/onboarding")}>Set Up Profile</Button>
        </Paper>
      </Box>
    );
  }

  const userSkills = profile.skills.map((s) => s.toLowerCase());

  // Domain coverage
  const domainAnalysis = SKILL_DOMAINS.map((d) => {
    const matched = d.skills.filter((s) => userSkills.some((us) => s.includes(us) || us.includes(s)));
    const coverage = Math.round((matched.length / d.skills.length) * 100);
    const coursesInDomain = allCourses.filter((c) =>
      c.skills.some((cs) => d.skills.some((ds) => cs.toLowerCase().includes(ds) || ds.includes(cs.toLowerCase())))
    );
    return { ...d, matched, coverage, courseCount: coursesInDomain.length };
  }).sort((a, b) => b.coverage - a.coverage);

  // Career alignment
  const careerAlignment = CAREER_PATHS.map((cp) => {
    const domainScores = cp.requiredDomains.map((rd) => {
      const da = domainAnalysis.find((d) => d.domain === rd);
      return da ? da.coverage : 0;
    });
    const avgScore = Math.round(domainScores.reduce((a, b) => a + b, 0) / domainScores.length);
    return { ...cp, score: avgScore, domainScores };
  }).sort((a, b) => b.score - a.score);

  // Skill gaps
  const skillGaps = domainAnalysis
    .filter((d) => d.coverage > 0 && d.coverage < 100)
    .map((d) => ({
      domain: d.domain,
      missing: d.skills.filter((s) => !userSkills.some((us) => s.includes(us) || us.includes(s))),
      courseCount: d.courseCount,
    }));

  return (
    <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 3 }}>
      <Typography variant="h5" fontWeight={700} mb={0.5}>Personal Analysis</Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Based on your profile — {profile.skills.length} skills, goal: {profile.motivation || "not set"}
      </Typography>

      <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Preview mode</strong> — Analysis is based on keyword matching with your profile.
          In Phase 3, AI Agents will provide deeper, contextual analysis using LLM interpretation.
        </Typography>
      </Alert>

      {/* Domain Coverage */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" fontWeight={700} fontSize={16} mb={2}>Skill Domain Coverage</Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}>
          {domainAnalysis.map((d) => (
            <Box key={d.domain} sx={{ flex: "1 1 calc(50% - 8px)", minWidth: 280 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                <Typography variant="body2" fontWeight={600}>{d.domain}</Typography>
                <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                  <Typography variant="caption" color="text.secondary">{d.courseCount} courses</Typography>
                  <Typography variant="caption" fontWeight={600} color={d.coverage >= 60 ? "#388e3c" : d.coverage >= 30 ? "#f57c00" : "#999"}>
                    {d.coverage}%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={d.coverage}
                sx={{
                  height: 8, borderRadius: 4, bgcolor: "#e0e0e0", mb: 0.5,
                  "& .MuiLinearProgress-bar": {
                    bgcolor: d.coverage >= 60 ? "#4caf50" : d.coverage >= 30 ? "#ff9800" : "#e0e0e0",
                    borderRadius: 4,
                  },
                }}
              />
              <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                {d.skills.map((s) => {
                  const has = userSkills.some((us) => s.includes(us) || us.includes(s));
                  return (
                    <Chip
                      key={s}
                      label={s}
                      size="small"
                      icon={has ? <CheckCircleIcon sx={{ fontSize: 14 }} /> : <RadioButtonUncheckedIcon sx={{ fontSize: 14 }} />}
                      sx={{
                        fontSize: 11,
                        bgcolor: has ? "#e8f5e9" : "#f5f5f5",
                        color: has ? "#388e3c" : "#999",
                        "& .MuiChip-icon": { color: has ? "#4caf50" : "#ccc" },
                      }}
                    />
                  );
                })}
              </Box>
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Career Alignment */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" fontWeight={700} fontSize={16} mb={2}>Career Path Alignment</Typography>
        <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
          {careerAlignment.map((cp) => (
            <Paper
              key={cp.title}
              variant="outlined"
              sx={{
                p: 2.5, minWidth: 240, flex: "1 1 0",
                borderColor: cp.score >= 50 ? "#6c63ff" : "#e0e0e0",
                bgcolor: cp.score >= 50 ? "#faf9ff" : "#fff",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, color: "#6c63ff" }}>
                {cp.icon}
                <Typography variant="subtitle2" fontWeight={600}>{cp.title}</Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <LinearProgress
                  variant="determinate" value={cp.score}
                  sx={{
                    flex: 1, height: 8, borderRadius: 4, bgcolor: "#e0e0e0",
                    "& .MuiLinearProgress-bar": { bgcolor: cp.score >= 50 ? "#6c63ff" : "#ff9800", borderRadius: 4 },
                  }}
                />
                <Typography variant="body2" fontWeight={700} fontSize={14}>{cp.score}%</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Requires: {cp.requiredDomains.join(", ")}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Paper>

      {/* Skills to Develop */}
      {skillGaps.length > 0 && (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Typography variant="h6" fontWeight={700} fontSize={16} mb={2}>Skills to Develop</Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}>
            {skillGaps.map((g) => (
              <Box key={g.domain} sx={{ flex: "1 1 calc(50% - 8px)", minWidth: 280 }}>
                <Typography variant="body2" fontWeight={600} mb={0.5}>{g.domain}</Typography>
                <Typography variant="caption" color="text.secondary" display="block" mb={0.75}>
                  {g.courseCount} courses available to fill these gaps
                </Typography>
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                  {g.missing.map((s) => (
                    <Chip
                      key={s}
                      label={s}
                      size="small"
                      onClick={() => navigate(`/search?q=${encodeURIComponent(s)}`)}
                      sx={{ fontSize: 11, bgcolor: "#fff3e0", color: "#f57c00", cursor: "pointer", "&:hover": { bgcolor: "#ffe0b2" } }}
                    />
                  ))}
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
      )}

      {/* Recommended Paths — horizontally scrollable */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" fontWeight={700} fontSize={16} mb={0.5}>Recommended Learning Paths</Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Curated course sequences to reach your career goals. Scroll to explore different paths.
        </Typography>

        <Box sx={{ display: "flex", gap: 3, overflowX: "auto", pb: 1 }}>
          {RECOMMENDED_PATHS.map((path) => (
            <Paper
              key={path.id}
              variant="outlined"
              sx={{
                p: 3,
                minWidth: 380,
                maxWidth: 420,
                flex: "0 0 auto",
                borderColor: "#e8e0ff",
                borderRadius: 3,
              }}
            >
              {/* Path header */}
              <Box sx={{ mb: 2, pb: 1.5, borderBottom: "1px solid #f0f0f0" }}>
                <Typography variant="subtitle1" fontWeight={700} fontSize={15}>
                  {path.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {path.description}
                </Typography>
              </Box>

              {/* Timeline steps */}
              <Box sx={{ position: "relative", pl: 3.5 }}>
                <Box
                  sx={{
                    position: "absolute",
                    left: 9,
                    top: 0,
                    bottom: 0,
                    width: 2,
                    bgcolor: "#e0e0e0",
                  }}
                />
                {path.steps.map((step, i) => (
                  <Box
                    key={i}
                    sx={{
                      position: "relative",
                      mb: i < path.steps.length - 1 ? 2.5 : 0,
                      p: 2,
                      bgcolor: "#fafafa",
                      borderRadius: 2,
                      "&::before": {
                        content: '""',
                        position: "absolute",
                        left: -23,
                        top: 18,
                        width: 10,
                        height: 10,
                        borderRadius: "50%",
                        bgcolor: "#6c63ff",
                        border: "2px solid #fff",
                        boxShadow: "0 0 0 2px #6c63ff",
                      },
                    }}
                  >
                    <Typography variant="caption" color="primary" fontWeight={600} letterSpacing={0.5}>
                      {step.label}
                    </Typography>
                    <Typography variant="subtitle2" fontWeight={600} fontSize={13}>
                      {step.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {step.org}
                    </Typography>
                    <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 0.75 }}>
                      {step.skills.map((s) => (
                        <Chip key={s} label={s} size="small" sx={{ fontSize: 10, height: 20, bgcolor: "#f5f3ff", color: "#6c63ff" }} />
                      ))}
                    </Box>
                    <Box
                      sx={{
                        mt: 1,
                        p: 1,
                        bgcolor: "#f5f3ff",
                        borderLeft: "3px solid #6c63ff",
                        borderRadius: "0 6px 6px 0",
                      }}
                    >
                      <Typography variant="caption" color="text.secondary" fontSize={11}>
                        {step.reason}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
