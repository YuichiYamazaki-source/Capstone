import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import Alert from "@mui/material/Alert";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

const skillGaps = [
  {
    name: "Python",
    current: 80,
    target: 90,
    color: "#4caf50",
    basis: "You listed Python as an existing skill. Target based on ML career requirements.",
  },
  {
    name: "Machine Learning",
    current: 30,
    target: 80,
    color: "#f44336",
    basis: "Interest area match. Low proficiency estimated from your current skill set.",
  },
  {
    name: "Data Visualization",
    current: 60,
    target: 85,
    color: "#ff9800",
    basis: "Related to Data Analysis skill. Gap identified for advanced roles.",
  },
  {
    name: "Statistics",
    current: 50,
    target: 75,
    color: "#ff9800",
    basis: "Foundation skill for ML path. Moderate gap estimated.",
  },
  {
    name: "Deep Learning",
    current: 10,
    target: 70,
    color: "#f44336",
    basis: "Advanced ML topic. Significant gap — this is a growth area.",
  },
];

const pathSteps = [
  {
    label: "Step 1 — Foundation",
    title: "Statistics for Data Science",
    org: "University of Michigan",
    skills: ["Statistics", "Probability", "Hypothesis Testing"],
    reason: "Fills your Statistics gap (50% → 75%). Required foundation before ML courses.",
  },
  {
    label: "Step 2 — Core",
    title: "Machine Learning Specialization",
    org: "Stanford Online",
    skills: ["Supervised Learning", "Neural Networks", "ML Algorithms"],
    reason: "Addresses your biggest skill gap in Machine Learning (30% → 80%). Builds on your Python strength.",
  },
  {
    label: "Step 3 — Advanced",
    title: "Deep Learning with TensorFlow",
    org: "Google Cloud",
    skills: ["Deep Learning", "TensorFlow", "Computer Vision"],
    reason: "Natural progression after ML fundamentals. Targets your Deep Learning gap (10% → 70%).",
  },
];

export default function LearningPath() {
  return (
    <Box sx={{ maxWidth: 1000, mx: "auto", p: { xs: 2, md: 4 } }}>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Your Learning Path
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Personalized roadmap based on your skill profile and goals.
      </Typography>

      <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Preview mode</strong> — Topics and progress shown below are sample data.
          In Phase 3, the Skill Gap Analysis Agent will generate these based on your
          actual profile and course data using LLM interpretation.
        </Typography>
      </Alert>

      {/* Skill Gap Analysis */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} mb={0.5}>
          Skill Gap Analysis
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={2}>
          Topics derived from your interests and career goals. Progress estimates based on
          your listed skills vs. target role requirements.
        </Typography>
        {skillGaps.map((skill) => (
          <Box key={skill.name} mb={2}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.25 }}>
              <Typography variant="body2" fontWeight={500}>{skill.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {skill.current}% → {skill.target}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={skill.current}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: "#e0e0e0",
                mb: 0.5,
                "& .MuiLinearProgress-bar": { bgcolor: skill.color, borderRadius: 4 },
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: "italic" }}>
              {skill.basis}
            </Typography>
          </Box>
        ))}
      </Paper>

      {/* Recommended Path */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} mb={0.5}>
          Recommended Path
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={3}>
          Ordered by prerequisite dependencies and your largest skill gaps.
        </Typography>
        <Box sx={{ position: "relative", pl: 4 }}>
          <Box
            sx={{
              position: "absolute",
              left: 11,
              top: 0,
              bottom: 0,
              width: 2,
              bgcolor: "#e0e0e0",
            }}
          />
          {pathSteps.map((step, i) => (
            <Box
              key={i}
              sx={{
                position: "relative",
                mb: 3,
                p: 2.5,
                bgcolor: "#fafafa",
                borderRadius: 3,
                "&::before": {
                  content: '""',
                  position: "absolute",
                  left: -27,
                  top: 24,
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  bgcolor: "#6c63ff",
                  border: "3px solid #fff",
                  boxShadow: "0 0 0 2px #6c63ff",
                },
              }}
            >
              <Typography variant="caption" color="primary" fontWeight={600} letterSpacing={1}>
                {step.label}
              </Typography>
              <Typography variant="subtitle2" fontWeight={600}>
                {step.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" fontSize={13}>
                {step.org}
              </Typography>
              <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 1 }}>
                {step.skills.map((s) => (
                  <Chip key={s} label={s} size="small" sx={{ fontSize: 11, bgcolor: "#f5f3ff", color: "#6c63ff" }} />
                ))}
              </Box>
              <Box
                sx={{
                  mt: 1.5,
                  p: 1.5,
                  bgcolor: "#f5f3ff",
                  borderLeft: "3px solid #6c63ff",
                  borderRadius: "0 8px 8px 0",
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {step.reason}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
