import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import Alert from "@mui/material/Alert";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import WorkIcon from "@mui/icons-material/Work";
import SchoolIcon from "@mui/icons-material/School";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";

const CAREER_ICONS = {
  default: <WorkIcon />,
  engineer: <TrendingUpIcon />,
  scientist: <TrendingUpIcon />,
  manager: <WorkIcon />,
  designer: <SchoolIcon />,
};

function getCareerIcon(role) {
  const lower = (role || "").toLowerCase();
  for (const [key, icon] of Object.entries(CAREER_ICONS)) {
    if (key !== "default" && lower.includes(key)) return icon;
  }
  return CAREER_ICONS.default;
}

export default function CareerContent({ data }) {
  if (data.error) {
    return <Alert severity="warning">{data.error}</Alert>;
  }

  const careers = data.career_paths || [];

  return (
    <Box>
      {data.recommendation && (
        <Typography variant="body2" color="text.secondary" mb={2}>
          {data.recommendation}
        </Typography>
      )}

      <Box sx={{ display: "flex", gap: 2, overflowX: "auto", pb: 1 }}>
        {careers.map((cp, i) => {
          const totalSkills = cp.required_skills?.length || 0;
          const userHas = cp.required_skills?.filter((s) => s.user_has).length || 0;
          const score = totalSkills > 0 ? Math.round((userHas / totalSkills) * 100) : 0;

          return (
            <Paper
              key={cp.role || i}
              variant="outlined"
              sx={{
                p: 2.5,
                minWidth: 280,
                flex: "1 1 0",
                borderColor: score >= 50 ? "#6c63ff" : "#e0e0e0",
                bgcolor: score >= 50 ? "#faf9ff" : "#fff",
                transition: "transform 0.2s, box-shadow 0.2s",
                "&:hover": { transform: "translateY(-2px)", boxShadow: 2 },
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, color: "#6c63ff" }}>
                {getCareerIcon(cp.role)}
                <Typography variant="subtitle2" fontWeight={600}>
                  {cp.role}
                </Typography>
              </Box>

              {cp.overview && (
                <Box sx={{ mb: 1 }}>
                  {cp.overview.demand && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Demand: {cp.overview.demand}
                    </Typography>
                  )}
                  {cp.overview.salary_range && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Salary: {cp.overview.salary_range}
                    </Typography>
                  )}
                </Box>
              )}

              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={score}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 4,
                    bgcolor: "#e0e0e0",
                    "& .MuiLinearProgress-bar": {
                      bgcolor: score >= 50 ? "#6c63ff" : "#ff9800",
                      borderRadius: 4,
                      transition: "width 1s ease-in-out",
                    },
                  }}
                />
                <Typography variant="body2" fontWeight={700} fontSize={14}>
                  {score}%
                </Typography>
              </Box>

              {cp.required_skills && (
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                  {cp.required_skills.map((s, j) => (
                    <Chip
                      key={s.skill || j}
                      label={s.skill}
                      size="small"
                      icon={
                        s.user_has ? (
                          <CheckCircleIcon sx={{ fontSize: 12 }} />
                        ) : (
                          <RadioButtonUncheckedIcon sx={{ fontSize: 12 }} />
                        )
                      }
                      sx={{
                        fontSize: 10,
                        bgcolor: s.user_has ? "#e8f5e9" : "#f5f5f5",
                        color: s.user_has ? "#388e3c" : "#999",
                        "& .MuiChip-icon": { color: s.user_has ? "#4caf50" : "#ccc" },
                      }}
                    />
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
