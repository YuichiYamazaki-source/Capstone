import { useState, useEffect } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import CloseIcon from "@mui/icons-material/Close";
import client from "../../api/client";
import PROFILE_STEPS, { SKILL_LEVELS } from "./profileSteps";

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export default function ProfileWizard({ open, onClose, onSave, initialProfile }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState(() => buildInitial(initialProfile));
  const [customInput, setCustomInput] = useState("");
  const [saving, setSaving] = useState(false);

  // Skill autocomplete state
  const [skillQuery, setSkillQuery] = useState("");
  const [skillOptions, setSkillOptions] = useState([]);
  const [topSkills, setTopSkills] = useState([]);
  const debouncedQuery = useDebounce(skillQuery, 300);

  const current = PROFILE_STEPS[step];

  useEffect(() => {
    if (open) {
      setStep(0);
      setAnswers(buildInitial(initialProfile));
      setCustomInput("");
      setSkillQuery("");
    }
  }, [open, initialProfile]);

  useEffect(() => {
    if (!open) return;
    client.get("/filters/skills", { params: { q: "", limit: 20 } })
      .then((res) => setTopSkills(res.data))
      .catch(() => {});
  }, [open]);

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

  function buildInitial(profile) {
    const p = profile || {};
    // Support both old (list[str]) and new (list[{name, level}]) formats
    const rawSkills = p.skills || [];
    const skills = rawSkills.map((s) =>
      typeof s === "string" ? { name: s, level: "Beginner" } : { ...s },
    );
    return {
      skills,
      motivation: p.motivation || null,
      learning_scope: p.learning_scope || null,
      learning_style: p.learning_style || null,
      interest_areas: Array.isArray(p.interest_areas) ? [...p.interest_areas] : [],
    };
  }

  // --- Skill name helpers ---
  const selectedSkillNames = answers.skills.map((s) => s.name);

  const toggleSkillName = (name) => {
    setAnswers((prev) => {
      const exists = prev.skills.find((s) => s.name === name);
      if (exists) {
        return { ...prev, skills: prev.skills.filter((s) => s.name !== name) };
      }
      return { ...prev, skills: [...prev.skills, { name, level: "Beginner" }] };
    });
  };

  const setSkillLevel = (name, level) => {
    setAnswers((prev) => ({
      ...prev,
      skills: prev.skills.map((s) =>
        s.name === name ? { ...s, level } : s,
      ),
    }));
  };

  // --- Generic chip helpers (non-autocomplete steps) ---
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

  const handleAddCustom = () => {
    const value = customInput.trim();
    if (!value) return;
    if (current.multi) {
      setAnswers((prev) => {
        const list = prev[current.key] || [];
        if (list.includes(value)) return prev;
        return { ...prev, [current.key]: [...list, value] };
      });
    } else {
      setAnswers((prev) => ({ ...prev, [current.key]: value }));
    }
    setCustomInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddCustom();
    }
  };

  // --- Navigation ---
  const handleNext = () => {
    setCustomInput("");
    setSkillQuery("");
    // Skip skill_levels step if no skills selected
    if (step === 0 && answers.skills.length === 0) {
      setStep(step + 2);
    } else if (step < PROFILE_STEPS.length - 1) {
      setStep(step + 1);
    } else {
      handleFinish();
    }
  };

  const handleBack = () => {
    setCustomInput("");
    setSkillQuery("");
    // Skip skill_levels step going back if no skills
    if (step === 2 && answers.skills.length === 0) {
      setStep(0);
    } else {
      setStep(step - 1);
    }
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      await onSave(answers);
    } finally {
      setSaving(false);
    }
  };

  // --- Render helpers ---
  const allOptions = current.multi && !current.autocomplete
    ? [
        ...current.options,
        ...(answers[current.key] || []).filter(
          (v) => !current.options.includes(v),
        ),
      ]
    : current.options || [];

  const showCustomAsChip =
    !current.multi &&
    !current.autocomplete &&
    current.type !== "skill_levels" &&
    answers[current.key] &&
    !(current.options || []).includes(answers[current.key]);

  const skillChips = current.autocomplete
    ? (() => {
        const topNames = topSkills.map((s) => s.skill);
        const extra = selectedSkillNames.filter((s) => !topNames.includes(s));
        return [...topNames, ...extra];
      })()
    : [];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { borderRadius: 3 } }}
    >
      <DialogTitle sx={{ pr: 6 }}>
        Edit Learning Profile
        <IconButton
          onClick={onClose}
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pb: 4 }}>
        <LinearProgress
          variant="determinate"
          value={((step + 1) / PROFILE_STEPS.length) * 100}
          sx={{ mb: 3, borderRadius: 2, height: 4 }}
        />

        <Typography variant="h6" fontWeight={700} gutterBottom>
          {current.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          {current.subtitle}
        </Typography>

        {current.autocomplete ? (
          /* --- Skill autocomplete step --- */
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
              Popular skills (click to toggle)
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
              <>
                <Typography variant="caption" color="text.secondary" mb={1} display="block">
                  Selected ({selectedSkillNames.length})
                </Typography>
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
              </>
            )}
          </>
        ) : current.type === "skill_levels" ? (
          /* --- Skill level rating step --- */
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 2 }}>
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
            {answers.skills.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No skills selected. Go back to add skills first.
              </Typography>
            )}
          </Box>
        ) : (
          /* --- Standard chip selection step --- */
          <>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
              {allOptions.map((opt) => (
                <Chip
                  key={opt}
                  label={opt}
                  variant={isSelected(opt) ? "filled" : "outlined"}
                  color={isSelected(opt) ? "primary" : "default"}
                  onClick={() => handleSelect(opt)}
                  sx={{ fontSize: 14, py: 2.5 }}
                />
              ))}
              {showCustomAsChip && (
                <Chip
                  label={answers[current.key]}
                  variant="filled"
                  color="primary"
                  onClick={() => handleSelect(answers[current.key])}
                  sx={{ fontSize: 14, py: 2.5 }}
                />
              )}
            </Box>

            <Box sx={{ display: "flex", gap: 1, mb: 3 }}>
              <TextField
                size="small"
                placeholder="Add your own..."
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                onKeyDown={handleKeyDown}
                fullWidth
              />
              <Button variant="outlined" size="small" onClick={handleAddCustom}>
                Add
              </Button>
            </Box>
          </>
        )}

        <Box sx={{ display: "flex", justifyContent: "space-between" }}>
          <Button variant="outlined" onClick={handleBack} disabled={step === 0}>
            Back
          </Button>
          <Button variant="contained" onClick={handleNext} disabled={saving}>
            {step === PROFILE_STEPS.length - 1
              ? saving ? "Saving..." : "Save"
              : "Next"}
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
