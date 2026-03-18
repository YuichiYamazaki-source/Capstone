import { useState, useCallback, useEffect, forwardRef } from "react";
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
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import CloseIcon from "@mui/icons-material/Close";
import PersonIcon from "@mui/icons-material/Person";
import { useAuth } from "../../contexts/AuthContext";
import client from "../../api/client";
import SkillGapContent from "../../components/analysis/SkillGapContent";
import CareerContent from "../../components/analysis/CareerContent";
import LearningPathContent from "../../components/analysis/LearningPathContent";

// Slide transition for modal (forwardRef required by MUI)
const SlideUp = forwardRef((props, ref) => <Slide direction="up" ref={ref} {...props} />);

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

  // Load saved results on mount
  useEffect(() => {
    if (!user?.id) return;
    const loadSaved = async () => {
      try {
        const res = await client.get(`/analyze/results/${user.id}`);
        const saved = res.data;
        if (saved.skill_gap) {
          setSkillGap({ data: saved.skill_gap.result, evidence: saved.skill_gap.evidence || "", loading: false, error: null, latency: saved.skill_gap.latency_ms });
        }
        if (saved.career) {
          setCareer({ data: saved.career.result, evidence: saved.career.evidence || "", loading: false, error: null, latency: saved.career.latency_ms });
        }
        if (saved.learning_path) {
          setLearningPath({ data: saved.learning_path.result, evidence: saved.learning_path.evidence || "", loading: false, error: null, latency: saved.learning_path.latency_ms });
        }
      } catch {
        // No saved results — keep default state
      }
    };
    loadSaved();
  }, [user?.id]);

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
        {skillGap.data && <SkillGapContent data={skillGap.data} onCourseClick={(title) => navigate(`/search?q=${encodeURIComponent(title)}`)} />}
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
      {isAnalyzed && <Fade in={isAnalyzed} timeout={500}><div>{children}</div></Fade>}
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

