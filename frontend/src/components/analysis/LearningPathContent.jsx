import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import Fade from "@mui/material/Fade";

export default function LearningPathContent({ data }) {
  if (data.error) {
    return <Alert severity="warning">{data.error}</Alert>;
  }

  const steps = data.path || [];
  const summary = data.summary || {};

  return (
    <Box>
      {data.goal && (
        <Typography variant="body2" color="text.secondary" mb={0.5}>
          Goal: {data.goal}
        </Typography>
      )}
      {summary.estimated_duration && (
        <Typography variant="caption" color="text.secondary" display="block" mb={2}>
          {summary.total_courses || steps.length} courses — Est. {summary.estimated_duration}
          {data.personalized && data.skipped_levels?.length > 0 && <> (skipped: {data.skipped_levels.join(", ")})</>}
        </Typography>
      )}

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
        {steps.map((step, i) => (
          <Fade in key={step.title || i} timeout={300 + i * 150}>
            <Box
              sx={{
                position: "relative",
                mb: i < steps.length - 1 ? 2.5 : 0,
                p: 2,
                bgcolor: "#fafafa",
                borderRadius: 2,
                transition: "background-color 0.2s",
                "&:hover": { bgcolor: "#f0f0f0" },
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
                Step {step.step || i + 1} — {step.level || ""}
              </Typography>
              <Typography variant="subtitle2" fontWeight={600} fontSize={13}>
                {step.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {step.organization}
                {step.rating && ` — ${step.rating} rating`}
                {step.duration && ` — ${step.duration}`}
              </Typography>
              {step.skills_acquired && (
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 0.75 }}>
                  {step.skills_acquired.map((s) => (
                    <Chip
                      key={s}
                      label={s}
                      size="small"
                      sx={{ fontSize: 10, height: 20, bgcolor: "#f5f3ff", color: "#6c63ff" }}
                    />
                  ))}
                </Box>
              )}
              {step.why && (
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
                    {step.why}
                  </Typography>
                </Box>
              )}
            </Box>
          </Fade>
        ))}
      </Box>
    </Box>
  );
}
