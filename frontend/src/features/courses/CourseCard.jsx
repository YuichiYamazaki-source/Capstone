import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import StarIcon from "@mui/icons-material/Star";

const levelColors = {
  Beginner: { bg: "#e8f5e9", color: "#388e3c" },
  Intermediate: { bg: "#e3f2fd", color: "#1976d2" },
  Advanced: { bg: "#fce4ec", color: "#c62828" },
};

export default function CourseCard({ course, reasons }) {
  const lc = levelColors[course.level] || { bg: "#f5f5f5", color: "#666" };

  return (
    <Paper
      sx={{
        p: 2.5,
        cursor: "pointer",
        transition: "all 0.2s",
        border: reasons?.length ? "1px solid #e8e0ff" : "1px solid #e0e0e0",
        bgcolor: reasons?.length ? "#faf9ff" : "#fff",
        "&:hover": {
          borderColor: "#6c63ff",
          boxShadow: "0 4px 16px rgba(108,99,255,0.15)",
        },
      }}
      elevation={0}
      onClick={() => course.url && window.open(course.url, "_blank")}
    >
      {/* Title + Rating */}
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="subtitle2" fontWeight={600} sx={{ flex: 1, lineHeight: 1.4 }}>
          {course.title}
        </Typography>
        {course.rating && (
          <Chip
            icon={<StarIcon sx={{ fontSize: 12 }} />}
            label={course.rating}
            size="small"
            sx={{ bgcolor: "#fff3e0", color: "#f57c00", fontWeight: 600, height: 22, fontSize: 11, ml: 1, flexShrink: 0 }}
          />
        )}
      </Box>

      {/* Organization */}
      <Typography variant="caption" color="text.secondary">
        {course.organization}
      </Typography>

      {/* Level badge */}
      <Box sx={{ display: "flex", gap: 0.5, mt: 1, flexWrap: "wrap" }}>
        <Chip
          label={course.level}
          size="small"
          sx={{ bgcolor: lc.bg, color: lc.color, fontSize: 11, height: 22 }}
        />
      </Box>

      {/* Why recommended */}
      {reasons?.length > 0 && (
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
          {reasons.map((r, i) => (
            <Typography key={i} variant="caption" display="block" color="text.secondary">
              {r}
            </Typography>
          ))}
        </Box>
      )}
    </Paper>
  );
}
