import { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import StarIcon from "@mui/icons-material/Star";
import { getCourses } from "./api";

function scoreMatch(course, profile) {
  let score = 0;
  const reasons = [];

  const userSkills = (profile.skills || []).map((s) => s.toLowerCase());
  const courseSkills = (course.skills || []).map((s) => s.toLowerCase());

  const overlap = courseSkills.filter((s) =>
    userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  if (overlap.length > 0) {
    score += overlap.length * 2;
    reasons.push(`Matches your skills: ${overlap.join(", ")}`);
  }

  const newSkills = courseSkills.filter(
    (s) => !userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  if (newSkills.length > 0) {
    score += newSkills.length;
    reasons.push(`New skills to learn: ${newSkills.join(", ")}`);
  }

  if (course.rating && course.rating >= 4.5) {
    score += 1;
    reasons.push("Highly rated course");
  }

  if (profile.motivation === "Career Change" && course.level === "Beginner") {
    score += 2;
    reasons.push("Good for career changers");
  }
  if (profile.motivation === "Skill Up at Current Job" && course.level === "Intermediate") {
    score += 2;
    reasons.push("Great for upskilling");
  }

  return { score, reasons };
}

export default function RecommendedSection({ courses, profile }) {
  const [allCourses, setAllCourses] = useState([]);

  useEffect(() => {
    getCourses({ limit: 50 })
      .then((data) => setAllCourses(data.courses))
      .catch(() => setAllCourses(courses));
  }, []);

  const source = allCourses.length > 0 ? allCourses : courses;

  const ranked = source
    .map((course) => {
      const { score, reasons } = scoreMatch(course, profile);
      return { ...course, score, reasons };
    })
    .filter((c) => c.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  if (ranked.length === 0) return null;

  const levelColors = {
    Beginner: { bg: "#e8f5e9", color: "#388e3c" },
    Intermediate: { bg: "#e3f2fd", color: "#1976d2" },
    Advanced: { bg: "#fce4ec", color: "#c62828" },
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <AutoAwesomeIcon sx={{ color: "#6c63ff", fontSize: 20 }} />
        <Typography variant="subtitle1" fontWeight={600}>
          Recommended for You
        </Typography>
      </Box>
      <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
        {ranked.map((course) => {
          const lc = levelColors[course.level] || { bg: "#f5f5f5", color: "#666" };
          return (
            <Paper
              key={course.id}
              sx={{
                p: 2.5,
                minWidth: 300,
                maxWidth: 360,
                flex: "0 0 auto",
                border: "1px solid #e8e0ff",
                bgcolor: "#faf9ff",
                cursor: "pointer",
                transition: "all 0.2s",
                "&:hover": {
                  borderColor: "#6c63ff",
                  boxShadow: "0 4px 16px rgba(108,99,255,0.15)",
                },
              }}
              onClick={() => course.url && window.open(course.url, "_blank")}
            >
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                <Typography variant="subtitle2" fontWeight={600} sx={{ flex: 1 }}>
                  {course.title}
                </Typography>
                {course.rating && (
                  <Chip
                    icon={<StarIcon sx={{ fontSize: 12 }} />}
                    label={course.rating}
                    size="small"
                    sx={{ bgcolor: "#fff3e0", color: "#f57c00", fontWeight: 600, height: 22, fontSize: 11 }}
                  />
                )}
              </Box>
              <Typography variant="caption" color="text.secondary">
                {course.organization}
              </Typography>
              <Box sx={{ display: "flex", gap: 0.5, mt: 1, flexWrap: "wrap" }}>
                <Chip
                  label={course.level}
                  size="small"
                  sx={{ bgcolor: lc.bg, color: lc.color, fontSize: 11, height: 22 }}
                />
              </Box>
              {course.reasons?.length > 0 && (
                <Box
                  sx={{
                    mt: 1.5,
                    p: 1.5,
                    bgcolor: "#f5f3ff",
                    borderLeft: "3px solid #6c63ff",
                    borderRadius: "0 8px 8px 0",
                  }}
                >
                  <Typography variant="caption" color="primary" fontWeight={600}>
                    Why recommended:
                  </Typography>
                  {course.reasons.map((r, i) => (
                    <Typography key={i} variant="caption" display="block" color="text.secondary">
                      {r}
                    </Typography>
                  ))}
                </Box>
              )}
            </Paper>
          );
        })}
      </Box>
    </Box>
  );
}
