import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import client from "../../api/client";
import { useAuth } from "../../contexts/AuthContext";
import PROFILE_STEPS, { SKILL_LEVELS } from "../profile/profileSteps";

const STEPS = PROFILE_STEPS;

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({ skills: [] });
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();

  // Skill autocomplete state
  const [skillQuery, setSkillQuery] = useState("");
  const [skillOptions, setSkillOptions] = useState([]);
  const [topSkills, setTopSkills] = useState([]);
  const debouncedQuery = useDebounce(skillQuery, 300);

  const current = STEPS[step];

  useEffect(() => {
    client.get("/filters/skills", { params: { q: "", limit: 20 } })
      .then((res) => setTopSkills(res.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!current?.autocomplete) return;
    if (!debouncedQuery) {
      setSkillOptions([]);
      return;
    }
    client.get("/filters/skills", { params: { q: debouncedQuery, limit: 20 } })
      .then((res) => setSkillOptions(res.data))
      .catch(() => setSkillOptions([]));
  }, [debouncedQuery, current?.autocomplete]);

  const selectedSkillNames = answers.skills.map((s) =>
    typeof s === "string" ? s : s.name,
  );

  const toggleSkillName = (name) => {
    setAnswers((prev) => {
      const exists = prev.skills.find(
        (s) => (typeof s === "string" ? s : s.name) === name,
      );
      if (exists) {
        return {
          ...prev,
          skills: prev.skills.filter(
            (s) => (typeof s === "string" ? s : s.name) !== name,
          ),
        };
      }
      return { ...prev, skills: [...prev.skills, { name, level: "Beginner" }] };
    });
  };

  const setSkillLevel = (name, level) => {
    setAnswers((prev) => ({
      ...prev,
      skills: prev.skills.map((s) =>
        (typeof s === "string" ? s : s.name) === name ? { name, level } : s,
      ),
    }));
  };

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
    setSkillQuery("");
    if (step === 0 && answers.skills.length === 0) {
      setStep(step + 2);
    } else if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      saveProfile();
    }
  };

  const handleBack = () => {
    setSkillQuery("");
    if (step === 2 && answers.skills.length === 0) {
      setStep(0);
    } else {
      setStep(step - 1);
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

  const skillChips = current?.autocomplete
    ? (() => {
        const topNames = topSkills.map((s) => s.skill);
        const extra = selectedSkillNames.filter((s) => !topNames.includes(s));
        return [...topNames, ...extra];
      })()
    : [];

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

        {current.autocomplete ? (
          <>
            <Autocomplete
              freeSolo
              options={skillOptions.map((s) => s.skill)}
              inputValue={skillQuery}
              onInputChange={(_, val) => setSkillQuery(val)}
              onChange={(_, val) => {
                if (val && !selectedSkillNames.includes(val)) {
                  toggleSkillName(val);
                }
                setSkillQuery("");
              }}
              renderOption={(props, option) => {
                const item = skillOptions.find((s) => s.skill === option);
                return (
                  <li {...props} key={option}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                      <span>{option}</span>
                      {item && (
                        <Typography variant="caption" color="text.secondary">
                          {item.count} courses
                        </Typography>
                      )}
                    </Box>
                  </li>
                );
              }}
              renderInput={(params) => (
                <TextField {...params} placeholder="Search skills..." size="small" />
              )}
              sx={{ mb: 2 }}
            />

            <Typography variant="caption" color="text.secondary" mb={1} display="block">
              Popular skills
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
              {skillChips.map((skill) => (
                <Chip
                  key={skill}
                  label={skill}
                  variant={selectedSkillNames.includes(skill) ? "filled" : "outlined"}
                  color={selectedSkillNames.includes(skill) ? "primary" : "default"}
                  onClick={() => toggleSkillName(skill)}
                  size="small"
                  sx={{ fontSize: 13 }}
                />
              ))}
            </Box>

            {selectedSkillNames.length > 0 && (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 2 }}>
                {answers.skills.map((s) => (
                  <Chip
                    key={s.name}
                    label={s.name}
                    color="primary"
                    size="small"
                    onDelete={() => toggleSkillName(s.name)}
                  />
                ))}
              </Box>
            )}
          </>
        ) : current.type === "skill_levels" ? (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 4 }}>
            {answers.skills.map((s) => (
              <Box
                key={s.name}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 2,
                  py: 1,
                  borderBottom: "1px solid #f0f0f0",
                }}
              >
                <Typography variant="body2" fontWeight={500} sx={{ minWidth: 140 }}>
                  {s.name}
                </Typography>
                <ToggleButtonGroup
                  value={s.level}
                  exclusive
                  onChange={(_, val) => { if (val) setSkillLevel(s.name, val); }}
                  size="small"
                >
                  {SKILL_LEVELS.map((lv) => (
                    <ToggleButton key={lv} value={lv} sx={{ textTransform: "none", px: 1.5 }}>
                      {lv}
                    </ToggleButton>
                  ))}
                </ToggleButtonGroup>
              </Box>
            ))}
          </Box>
        ) : (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 4 }}>
            {(current.options || []).map((opt) => (
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
        )}

        <Box sx={{ display: "flex", justifyContent: "space-between" }}>
          <Button color="inherit" onClick={skip} sx={{ color: "#888" }}>
            Skip for now
          </Button>
          <Box sx={{ display: "flex", gap: 1 }}>
            {step > 0 && (
              <Button variant="outlined" onClick={handleBack}>
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
