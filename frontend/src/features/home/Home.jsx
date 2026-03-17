import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import IconButton from "@mui/material/IconButton";
import ExploreIcon from "@mui/icons-material/Explore";
import RouteIcon from "@mui/icons-material/Route";
import EditIcon from "@mui/icons-material/Edit";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import SchoolIcon from "@mui/icons-material/School";
import StarIcon from "@mui/icons-material/Star";
import WorkIcon from "@mui/icons-material/Work";
import PlayCircleOutlineIcon from "@mui/icons-material/PlayCircleOutline";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { useAuth } from "../../contexts/AuthContext";
import { getCourses } from "../courses/api";

function scoreMatch(course, profile) {
  let score = 0;
  const userSkills = (profile.skills || []).map((s) => s.toLowerCase());
  const courseSkills = (course.skills || []).map((s) => s.toLowerCase());
  const overlap = courseSkills.filter((s) =>
    userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  score += overlap.length * 2;
  const newSkills = courseSkills.filter(
    (s) => !userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  score += newSkills.length;
  if (course.rating && course.rating >= 4.5) score += 1;
  if (profile.motivation === "Career Change" && course.level === "Beginner") score += 2;
  if (profile.motivation === "Skill Up at Current Job" && course.level === "Intermediate") score += 2;
  return score;
}

const LEVEL_COLORS = {
  Beginner: { bg: "#e8f5e9", color: "#388e3c" },
  Intermediate: { bg: "#e3f2fd", color: "#1976d2" },
  Advanced: { bg: "#fce4ec", color: "#c62828" },
};

const MOTIVATION_INSIGHTS = {
  "Career Change": {
    tip: "Focus on foundational courses to build core skills in your target field.",
    icon: <WorkIcon />,
  },
  "Skill Up at Current Job": {
    tip: "Look for intermediate courses that deepen skills relevant to your current role.",
    icon: <TrendingUpIcon />,
  },
  "Hobby / Personal Interest": {
    tip: "Explore freely! Start with topics that excite you and branch out from there.",
    icon: <ExploreIcon />,
  },
  "Academic / Certification": {
    tip: "Prioritize accredited courses with certificates to strengthen your credentials.",
    icon: <SchoolIcon />,
  },
};

// Stub enrolled courses
const ENROLLED_STUB = [
  { id: "e1", title: "Introduction to Data Analysis with Python", org: "University of Michigan", progress: 65, level: "Beginner" },
  { id: "e2", title: "Machine Learning Foundations", org: "Stanford University", progress: 20, level: "Intermediate" },
  { id: "e3", title: "Cloud Computing Basics", org: "Google Cloud", progress: 100, level: "Beginner" },
];

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const profile = user?.profile;
  const [topCourses, setTopCourses] = useState([]);
  const [allCourses, setAllCourses] = useState([]);

  const hasProfile = profile?.skills?.length > 0;

  useEffect(() => {
    getCourses({ limit: 50 })
      .then((data) => {
        setAllCourses(data.courses);
        if (hasProfile) {
          const ranked = data.courses
            .map((c) => ({ ...c, matchScore: scoreMatch(c, profile) }))
            .sort((a, b) => b.matchScore - a.matchScore)
            .slice(0, 5);
          setTopCourses(ranked);
        } else {
          setTopCourses(data.courses.slice(0, 5));
        }
      })
      .catch(() => {});
  }, []);

  const motivationInsight = profile?.motivation ? MOTIVATION_INSIGHTS[profile.motivation] : null;
  const enrolledCourses = user ? ENROLLED_STUB : [];
  const inProgress = enrolledCourses.filter((c) => c.progress < 100);
  const completed = enrolledCourses.filter((c) => c.progress === 100);

  return (
    <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 3 }}>
      {/* Welcome header */}
      <Box mb={3}>
        <Typography variant="h5" fontWeight={700}>
          {user ? `Welcome back, ${user.name}` : "Welcome to Course Finder"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your hub for intelligent course discovery
        </Typography>
      </Box>

      {/* === Section 1: Profile banner (full-width horizontal) === */}
      {user && hasProfile && (
        <Paper
          sx={{
            background: "linear-gradient(135deg, #6c63ff, #5a52d5)",
            borderRadius: 3,
            p: 3,
            color: "#fff",
            mb: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 3,
          }}
        >
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <Typography variant="subtitle1" fontWeight={600}>Your Profile</Typography>
              <Button
                size="small"
                startIcon={<EditIcon sx={{ fontSize: 14 }} />}
                onClick={() => navigate("/profile")}
                sx={{ color: "#fff", bgcolor: "rgba(255,255,255,0.15)", fontSize: 11, "&:hover": { bgcolor: "rgba(255,255,255,0.25)" } }}
              >
                Edit
              </Button>
            </Box>
            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 1 }}>
              {profile.skills.map((s) => (
                <Chip key={s} label={s} size="small" sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "#fff", fontSize: 11 }} />
              ))}
            </Box>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              {profile.motivation && <Chip label={`Goal: ${profile.motivation}`} size="small" sx={{ bgcolor: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.9)", fontSize: 11 }} />}
              {profile.learning_scope && <Chip label={`Scope: ${profile.learning_scope}`} size="small" sx={{ bgcolor: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.9)", fontSize: 11 }} />}
              {profile.learning_style && <Chip label={`Style: ${profile.learning_style}`} size="small" sx={{ bgcolor: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.9)", fontSize: 11 }} />}
            </Box>
          </Box>
          {motivationInsight && (
            <Paper sx={{ p: 2, minWidth: 280, maxWidth: 340, bgcolor: "rgba(255,255,255,0.95)", borderRadius: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.75, color: "#6c63ff" }}>
                {motivationInsight.icon}
                <Typography variant="subtitle2" fontWeight={600} fontSize={13} color="#6c63ff">
                  Personalized Insight
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" fontSize={12} lineHeight={1.6}>
                {motivationInsight.tip}
              </Typography>
              <Box sx={{ mt: 1, display: "flex", gap: 1, alignItems: "center" }}>
                <Chip label={`${allCourses.length} courses`} size="small" variant="outlined" sx={{ fontSize: 10, height: 22 }} />
                <Chip label={`${profile.skills.length} skills`} size="small" variant="outlined" sx={{ fontSize: 10, height: 22 }} />
                <Button
                  size="small"
                  endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />}
                  onClick={() => navigate("/analysis")}
                  sx={{ ml: "auto", fontSize: 11, color: "#6c63ff", fontWeight: 600, textTransform: "none" }}
                >
                  View Analysis
                </Button>
              </Box>
            </Paper>
          )}
        </Paper>
      )}

      {/* === Section 2: My Courses (Udemy style — full-width, horizontal cards) === */}
      {enrolledCourses.length > 0 && (
        <Box mb={3}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h6" fontWeight={700} fontSize={18}>My Courses</Typography>
            <Button size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />} sx={{ fontSize: 13 }}>
              View all
            </Button>
          </Box>

          {/* In progress */}
          {inProgress.length > 0 && (
            <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1, mb: 1 }}>
              {inProgress.map((c) => {
                const lc = LEVEL_COLORS[c.level] || { bg: "#f5f5f5", color: "#666" };
                return (
                  <Paper
                    key={c.id}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      p: 2,
                      minWidth: 420,
                      flex: "1 1 0",
                      cursor: "pointer",
                      transition: "all 0.15s",
                      "&:hover": { boxShadow: "0 4px 16px rgba(0,0,0,0.08)" },
                    }}
                  >
                    {/* Thumbnail placeholder */}
                    <Box sx={{ width: 100, height: 70, bgcolor: "#ede7f6", borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <PlayCircleOutlineIcon sx={{ fontSize: 32, color: "#6c63ff" }} />
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight={600} mb={0.25}>{c.title}</Typography>
                      <Typography variant="caption" color="text.secondary">{c.org}</Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={c.progress}
                          sx={{ flex: 1, height: 6, borderRadius: 3, bgcolor: "#e0e0e0", "& .MuiLinearProgress-bar": { bgcolor: "#6c63ff", borderRadius: 3 } }}
                        />
                        <Typography variant="caption" fontWeight={600} color="text.secondary">{c.progress}%</Typography>
                      </Box>
                    </Box>
                    <IconButton size="small"><MoreVertIcon fontSize="small" /></IconButton>
                  </Paper>
                );
              })}
            </Box>
          )}

          {/* Completed */}
          {completed.length > 0 && (
            <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
              {completed.map((c) => (
                <Paper
                  key={c.id}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    p: 2,
                    minWidth: 420,
                    flex: "1 1 0",
                    opacity: 0.85,
                    cursor: "pointer",
                  }}
                >
                  <Box sx={{ width: 100, height: 70, bgcolor: "#e8f5e9", borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <CheckCircleOutlineIcon sx={{ fontSize: 32, color: "#4caf50" }} />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight={600} mb={0.25}>{c.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{c.org}</Typography>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
                      <CheckCircleOutlineIcon sx={{ fontSize: 14, color: "#4caf50" }} />
                      <Typography variant="caption" color="#4caf50" fontWeight={600}>Completed</Typography>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* === Section 3: Learning Insight (full-width horizontal banner) === */}
      {user && hasProfile && (
        <Paper
          sx={{
            p: 2.5,
            mb: 3,
            display: "flex",
            alignItems: "center",
            gap: 3,
            border: "1px solid #e0e0e0",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, color: "#6c63ff" }}>
            <AccessTimeIcon />
            <Box>
              <Typography variant="subtitle2" fontWeight={600}>Set a learning schedule</Typography>
              <Typography variant="body2" color="text.secondary" fontSize={13}>
                Consistent learners are 3x more likely to reach their goals. Set aside time each day to build habits.
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: "flex", gap: 1, flexShrink: 0 }}>
            <Button variant="outlined" size="small" sx={{ fontSize: 12 }}>
              Start
            </Button>
            <Button size="small" color="inherit" sx={{ fontSize: 12, color: "#888" }}>
              Dismiss
            </Button>
          </Box>
        </Paper>
      )}

      {/* === Section 4: Recommended for You (full-width, horizontal scroll) === */}
      <Box mb={3}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <AutoAwesomeIcon sx={{ color: "#6c63ff", fontSize: 20 }} />
            <Typography variant="h6" fontWeight={700} fontSize={18}>
              {hasProfile ? "Recommended for You" : "Popular Courses"}
            </Typography>
          </Box>
          <Button size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />} onClick={() => navigate("/search")} sx={{ fontSize: 13 }}>
            Browse all
          </Button>
        </Box>
        <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
          {topCourses.map((course) => {
            const lc = LEVEL_COLORS[course.level] || { bg: "#f5f5f5", color: "#666" };
            return (
              <Paper
                key={course.id}
                sx={{
                  minWidth: 260,
                  maxWidth: 300,
                  flex: "1 1 0",
                  cursor: "pointer",
                  transition: "all 0.15s",
                  overflow: "hidden",
                  "&:hover": { boxShadow: "0 4px 20px rgba(0,0,0,0.1)", transform: "translateY(-2px)" },
                }}
                onClick={() => course.url && window.open(course.url, "_blank")}
              >
                {/* Thumbnail placeholder */}
                <Box sx={{ height: 120, bgcolor: "#ede7f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <SchoolIcon sx={{ fontSize: 40, color: "#6c63ff", opacity: 0.5 }} />
                </Box>
                <Box sx={{ p: 2 }}>
                  <Typography variant="body2" fontWeight={600} mb={0.5} sx={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {course.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                    {course.organization}
                  </Typography>
                  <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
                    {course.rating && (
                      <Chip icon={<StarIcon sx={{ fontSize: 12 }} />} label={course.rating} size="small"
                        sx={{ bgcolor: "#fff3e0", color: "#f57c00", fontWeight: 600, height: 22, fontSize: 11 }} />
                    )}
                    <Chip label={course.level} size="small" sx={{ bgcolor: lc.bg, color: lc.color, height: 22, fontSize: 11 }} />
                  </Box>
                </Box>
              </Paper>
            );
          })}
        </Box>
      </Box>

      {/* === Section 5: Quick Actions (full-width horizontal) === */}
      <Box sx={{ display: "flex", gap: 2 }}>
        {[
          { icon: <ExploreIcon />, title: "Explore & Consult", desc: "Chat with AI to discover courses matching your goals.", path: "/explore", color: "#ede7f6", iconColor: "#6c63ff", badge: "AI-Powered" },
          { icon: <RouteIcon />, title: "Learning Path", desc: "Get a personalized roadmap based on your skill gaps.", path: "/analysis", color: "#e8f5e9", iconColor: "#388e3c", badge: "AI-Powered" },
          { icon: <EmojiEventsIcon />, title: "Skill Coverage", desc: `${profile?.skills?.length || 0} skills tracked across ${allCourses.length} courses in the catalog.`, path: "/search", color: "#fff3e0", iconColor: "#f57c00" },
        ].map((f) => (
          <Paper
            key={f.path + f.title}
            onClick={() => navigate(f.path)}
            sx={{
              flex: 1,
              p: 2.5,
              cursor: "pointer",
              border: "2px solid transparent",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: 2,
              "&:hover": { borderColor: "#6c63ff", boxShadow: "0 4px 16px rgba(108,99,255,0.12)" },
            }}
          >
            <Box sx={{ width: 44, height: 44, borderRadius: 2, bgcolor: f.color, color: f.iconColor, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              {f.icon}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="subtitle2" fontWeight={600} fontSize={14}>{f.title}</Typography>
                {f.badge && <Chip label={f.badge} size="small" color="primary" sx={{ fontSize: 10, height: 20 }} />}
              </Box>
              <Typography variant="caption" color="text.secondary">{f.desc}</Typography>
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
}
