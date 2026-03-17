import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import client from "../../api/client";
import { useAuth } from "../../contexts/AuthContext";

const STEPS = [
  {
    title: "What skills do you already have?",
    subtitle: "Select all that apply",
    key: "skills",
    multi: true,
    options: [
      "Python", "Data Analysis", "Machine Learning", "SQL",
      "JavaScript", "Cloud Computing", "Project Management",
      "Communication", "Leadership", "Cybersecurity",
    ],
  },
  {
    title: "What brings you here?",
    subtitle: "Understanding your motivation helps us recommend better.",
    key: "motivation",
    multi: false,
    options: [
      "Career Change", "Skill Up at Current Job",
      "Hobby / Personal Interest", "Academic / Certification",
    ],
  },
  {
    title: "How deep do you want to go?",
    subtitle: "This helps us calibrate the scope of recommendations.",
    key: "learning_scope",
    multi: false,
    options: [
      "Single Course", "A Few Related Courses",
      "Full Learning Path", "Not Sure Yet",
    ],
  },
  {
    title: "How do you learn best?",
    subtitle: "We'll match your style with the right courses.",
    key: "learning_style",
    multi: false,
    options: [
      "Video Lectures", "Hands-on Projects",
      "Reading / Articles", "Interactive Exercises",
    ],
  },
];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({ skills: [] });
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();

  const current = STEPS[step];

  const handleSelect = (option) => {
    if (current.multi) {
      setAnswers((prev) => {
        const list = prev[current.key] || [];
        return {
          ...prev,
          [current.key]: list.includes(option)
            ? list.filter((x) => x !== option)
            : [...list, option],
        };
      });
    } else {
      setAnswers((prev) => ({
        ...prev,
        [current.key]: prev[current.key] === option ? null : option,
      }));
    }
  };

  const isSelected = (option) => {
    const val = answers[current.key];
    return Array.isArray(val) ? val.includes(option) : val === option;
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      saveProfile();
    }
  };

  const saveProfile = async () => {
    try {
      const res = await client.put("/users/profile", answers);
      if (user) {
        updateUser({ ...user, profile: res.data.profile });
      }
    } catch {
      // continue even if save fails
    }
    navigate("/");
  };

  const skip = () => navigate("/");

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "calc(100vh - 64px)",
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        p: 3,
      }}
    >
      <Paper sx={{ p: 6, maxWidth: 640, width: "100%", borderRadius: 4 }}>
        <LinearProgress
          variant="determinate"
          value={((step + 1) / STEPS.length) * 100}
          sx={{ mb: 4, borderRadius: 2, height: 4 }}
        />

        <Typography variant="h5" fontWeight={700} gutterBottom>
          {current.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          {current.subtitle}
        </Typography>

        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 4 }}>
          {current.options.map((opt) => (
            <Chip
              key={opt}
              label={opt}
              variant={isSelected(opt) ? "filled" : "outlined"}
              color={isSelected(opt) ? "primary" : "default"}
              onClick={() => handleSelect(opt)}
              sx={{ fontSize: 14, py: 2.5 }}
            />
          ))}
        </Box>

        <Box sx={{ display: "flex", justifyContent: "space-between" }}>
          <Button color="inherit" onClick={skip} sx={{ color: "#888" }}>
            Skip for now
          </Button>
          <Box sx={{ display: "flex", gap: 1 }}>
            {step > 0 && (
              <Button variant="outlined" onClick={() => setStep(step - 1)}>
                Back
              </Button>
            )}
            <Button variant="contained" onClick={handleNext}>
              {step === STEPS.length - 1 ? "Finish" : "Next"}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
