import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";

export default function SkillGapContent({ data, onCourseClick }) {
  if (data.error) {
    return <Alert severity="warning">{data.error}</Alert>;
  }

  const gaps = data.gaps || [];
  const currentSkills = data.current_skills || [];

  return (
    <Box>
      {data.target_role && (
        <Typography variant="body2" color="text.secondary" mb={1}>
          Target: {data.target_role} — {currentSkills.length} current skills, {gaps.length} gaps
        </Typography>
      )}
      {data.summary && (
        <Typography variant="body2" mb={2}>
          {data.summary}
        </Typography>
      )}

      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}>
        {gaps.map((gap, i) => (
          <Box key={gap.skill || i} sx={{ flex: "1 1 calc(50% - 8px)", minWidth: 280 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
              <Typography variant="body2" fontWeight={600}>
                {gap.skill}
              </Typography>
              <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
                {gap.priority && (
                  <Chip
                    label={`P${gap.priority}`}
                    size="small"
                    sx={{
                      fontSize: 10,
                      height: 20,
                      bgcolor: gap.priority <= 2 ? "#ffebee" : "#fff3e0",
                      color: gap.priority <= 2 ? "#c62828" : "#e65100",
                    }}
                  />
                )}
                {gap.match_type && (
                  <Chip
                    label={gap.match_type}
                    size="small"
                    icon={
                      gap.match_type === "matched" ? (
                        <CheckCircleIcon sx={{ fontSize: 12 }} />
                      ) : (
                        <RadioButtonUncheckedIcon sx={{ fontSize: 12 }} />
                      )
                    }
                    sx={{
                      fontSize: 10,
                      height: 20,
                      bgcolor: gap.match_type === "matched" ? "#e8f5e9" : "#fff8e1",
                      color: gap.match_type === "matched" ? "#2e7d32" : "#f57f17",
                      "& .MuiChip-icon": {
                        color: gap.match_type === "matched" ? "#4caf50" : "#ffc107",
                      },
                    }}
                  />
                )}
              </Box>
            </Box>
            {gap.reason && (
              <Typography variant="caption" color="text.secondary" display="block" mb={0.75}>
                {gap.reason}
              </Typography>
            )}
            {gap.note && (
              <Typography variant="caption" color="warning.main" display="block" mb={0.75}>
                {gap.note}
              </Typography>
            )}
            {gap.courses?.length > 0 && (
              <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                {gap.courses.map((course, j) => (
                  <Chip
                    key={course.title || j}
                    label={`${course.title} (${course.organization})`}
                    size="small"
                    onClick={() => onCourseClick?.(course.title)}
                    sx={{
                      fontSize: 11,
                      bgcolor: "#f5f3ff",
                      color: "#6c63ff",
                      cursor: onCourseClick ? "pointer" : "default",
                      "&:hover": onCourseClick ? { bgcolor: "#ede7f6" } : {},
                    }}
                  />
                ))}
              </Box>
            )}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
