import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Alert from "@mui/material/Alert";
import Skeleton from "@mui/material/Skeleton";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import IconButton from "@mui/material/IconButton";
import Fade from "@mui/material/Fade";
import Slide from "@mui/material/Slide";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import WorkIcon from "@mui/icons-material/Work";
import SchoolIcon from "@mui/icons-material/School";
import RefreshIcon from "@mui/icons-material/Refresh";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import CloseIcon from "@mui/icons-material/Close";
import PersonIcon from "@mui/icons-material/Person";
import { useAuth } from "../../contexts/AuthContext";
import client from "../../api/client";

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

// Slide transition for modal
const SlideUp = (props) => <Slide direction="up" {...props} />;

export default function Analysis() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const profile = user?.profile;

  // Each section has independent state
  const [skillGap, setSkillGap] = useState({ data: null, evidence: "", loading: false, error: null, latency: 0 });
  const [career, setCareer] = useState({ data: null, evidence: "", loading: false, error: null, latency: 0 });
  const [learningPath, setLearningPath] = useState({ data: null, evidence: "", loading: false, error: null, latency: 0 });

  // Evidence modal state
  const [evidenceModal, setEvidenceModal] = useState({ open: false, title: "", content: "" });

  const runAnalysis = useCallback(
    async (type, setter) => {
      if (!user?.id) return;
      setter((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const res = await client.post(`/analyze/${type}`, { user_id: user.id });
        setter({
          data: res.data.result,
          evidence: res.data.evidence || "",
          loading: false,
          error: null,
          latency: res.data.latency_ms,
        });
      } catch (err) {
        const detail = err.response?.data?.detail || "Analysis failed. Please try again.";
        setter((prev) => ({ ...prev, loading: false, error: detail }));
      }
    },
    [user?.id],
  );

  if (!user) {
    navigate("/login");
    return null;
  }

  if (!profile?.skills?.length) {
    return (
      <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 4 }}>
        <Typography variant="h5" fontWeight={700} mb={2}>
          Personal Analysis
        </Typography>
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <Typography variant="body1" mb={2}>
            Complete your profile to see personalized analysis.
          </Typography>
          <Button variant="contained" onClick={() => navigate("/onboarding")}>
            Set Up Profile
          </Button>
        </Paper>
      </Box>
    );
  }

  const openEvidence = (title, content) => {
    setEvidenceModal({ open: true, title, content });
  };

  return (
    <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 3 }}>
      {/* Header */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
        <Typography variant="h5" fontWeight={700}>
          Personal Analysis
        </Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<PersonIcon />}
          onClick={() => navigate("/profile")}
          sx={{ borderColor: "#6c63ff", color: "#6c63ff" }}
        >
          Edit Profile
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" mb={3}>
        {profile.skills.length} skills registered — Goal: {profile.motivation || "not set"}
      </Typography>

      {/* Skill Gap Section */}
      <AnalysisSection
        title="Skill Gap Analysis"
        icon={<TrendingUpIcon sx={{ fontSize: 20, color: "#6c63ff" }} />}
        state={skillGap}
        onAnalyze={() => runAnalysis("skill-gap", setSkillGap)}
        onShowEvidence={() => openEvidence("Skill Gap Analysis — Evidence", skillGap.evidence)}
      >
        {skillGap.data && <SkillGapContent data={skillGap.data} navigate={navigate} />}
      </AnalysisSection>

      {/* Career Section */}
      <AnalysisSection
        title="Career Path Alignment"
        icon={<WorkIcon sx={{ fontSize: 20, color: "#6c63ff" }} />}
        state={career}
        onAnalyze={() => runAnalysis("career", setCareer)}
        onShowEvidence={() => openEvidence("Career Path Alignment — Evidence", career.evidence)}
      >
        {career.data && <CareerContent data={career.data} />}
      </AnalysisSection>

      {/* Learning Path Section */}
      <AnalysisSection
        title="Recommended Learning Path"
        icon={<SchoolIcon sx={{ fontSize: 20, color: "#6c63ff" }} />}
        state={learningPath}
        onAnalyze={() => runAnalysis("learning-path", setLearningPath)}
        onShowEvidence={() => openEvidence("Recommended Learning Path — Evidence", learningPath.evidence)}
      >
        {learningPath.data && <LearningPathContent data={learningPath.data} />}
      </AnalysisSection>

      {/* Evidence Modal */}
      <EvidenceModal
        open={evidenceModal.open}
        title={evidenceModal.title}
        content={evidenceModal.content}
        onClose={() => setEvidenceModal({ open: false, title: "", content: "" })}
      />
    </Box>
  );
}

function AnalysisSection({ title, icon, state, onAnalyze, onShowEvidence, children }) {
  const { data, loading, error, latency } = state;
  const hasEvidence = state.evidence && state.evidence.trim().length > 0;
  const isAnalyzed = data !== null;

  return (
    <Paper sx={{ p: 3, mb: 2, transition: "box-shadow 0.3s", "&:hover": { boxShadow: 3 } }}>
      {/* Section header */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: isAnalyzed ? 2 : 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          {icon}
          <Typography variant="h6" fontWeight={700} fontSize={16}>
            {title}
          </Typography>
          {latency > 0 && (
            <Chip
              label={`${(latency / 1000).toFixed(1)}s`}
              size="small"
              sx={{ fontSize: 10, height: 20, bgcolor: "#e0f2f1", color: "#00695c" }}
            />
          )}
        </Box>
        <Box sx={{ display: "flex", gap: 1 }}>
          {hasEvidence && (
            <Button
              variant="text"
              size="small"
              startIcon={<InfoOutlinedIcon />}
              onClick={onShowEvidence}
              sx={{ color: "#6c63ff", fontSize: 12 }}
            >
              Evidence
            </Button>
          )}
          <Button
            variant={isAnalyzed ? "outlined" : "contained"}
            size="small"
            startIcon={loading ? <CircularProgress size={14} /> : isAnalyzed ? <RefreshIcon /> : <PlayArrowIcon />}
            onClick={onAnalyze}
            disabled={loading}
            sx={
              isAnalyzed
                ? { borderColor: "#6c63ff", color: "#6c63ff" }
                : { bgcolor: "#6c63ff", "&:hover": { bgcolor: "#5a52d5" } }
            }
          >
            {loading ? "Analyzing..." : isAnalyzed ? "Refresh" : "Analyze"}
          </Button>
        </Box>
      </Box>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading skeleton */}
      {loading && !data && (
        <Box>
          <Skeleton variant="text" width="40%" height={24} />
          <Skeleton variant="rectangular" height={100} sx={{ mt: 1, borderRadius: 1 }} />
        </Box>
      )}

      {/* Not analyzed yet */}
      {!isAnalyzed && !loading && !error && (
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
          Not analyzed yet. Click "Analyze" to run AI-powered analysis.
        </Typography>
      )}

      {/* Content */}
      {isAnalyzed && <Fade in={isAnalyzed} timeout={500}>{children}</Fade>}
    </Paper>
  );
}

function EvidenceModal({ open, title, content, onClose }) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      TransitionComponent={SlideUp}
      PaperProps={{ sx: { borderRadius: 3, maxHeight: "80vh" } }}
    >
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", pb: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <InfoOutlinedIcon sx={{ color: "#6c63ff" }} />
          <Typography variant="h6" fontSize={16} fontWeight={700}>
            {title}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        {content ? (
          <Typography
            variant="body2"
            sx={{
              whiteSpace: "pre-wrap",
              lineHeight: 1.8,
              "& strong": { color: "#6c63ff" },
            }}
          >
            {content}
          </Typography>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
            No detailed evidence available for this analysis.
          </Typography>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 1.5 }}>
        <Button onClick={onClose} sx={{ color: "#6c63ff" }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function SkillGapContent({ data, navigate }) {
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
                    onClick={() => navigate(`/search?q=${encodeURIComponent(course.title)}`)}
                    sx={{
                      fontSize: 11,
                      bgcolor: "#f5f3ff",
                      color: "#6c63ff",
                      cursor: "pointer",
                      "&:hover": { bgcolor: "#ede7f6" },
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

function CareerContent({ data }) {
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

function LearningPathContent({ data }) {
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
