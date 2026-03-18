import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import { useAuth } from "../../contexts/AuthContext";
import { getProfile, updateProfile } from "./api";
import ProfileWizard from "./ProfileWizard";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    fetchProfile();
  }, [user]);

  const fetchProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
    } catch {
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (answers) => {
    const payload = {
      skills: answers.skills || [],
      motivation: answers.motivation || null,
      learning_scope: answers.learning_scope || null,
      learning_style: answers.learning_style || null,
      interest_areas: answers.interest_areas || [],
    };
    const data = await updateProfile(payload);
    setProfile(data);
    updateUser({ ...user, profile: data.profile });
    setWizardOpen(false);
    setMessage("Profile updated!");
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", p: { xs: 2, md: 4 } }}>
      <Typography variant="h5" fontWeight={700} mb={3}>
        My Profile
      </Typography>

      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage("")}>
          {message}
        </Alert>
      )}

      <Paper sx={{ p: 3.5, mb: 2.5 }}>
        <Typography variant="subtitle2" fontWeight={600} mb={2}>
          Account
        </Typography>
        <ProfileField label="Name" value={profile?.name} />
        <ProfileField label="Email" value={profile?.email} />
        <ProfileField label="Member since" value={profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "—"} />
      </Paper>

      <Paper sx={{ p: 3.5, mb: 2.5 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="subtitle2" fontWeight={600}>
            Learning Profile
          </Typography>
          <Button size="small" onClick={() => setWizardOpen(true)}>
            Edit
          </Button>
        </Box>

        <ProfileField label="Skills" value={
          profile?.profile?.skills?.length > 0
            ? <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                {profile.profile.skills.map((s) => {
                  const name = typeof s === "string" ? s : s.name;
                  const level = typeof s === "string" ? null : s.level;
                  return (
                    <Chip
                      key={name}
                      label={level ? `${name} (${level})` : name}
                      size="small"
                    />
                  );
                })}
              </Box>
            : "Not set"
        } />
        <ProfileField label="Motivation" value={profile?.profile?.motivation || "Not set"} />
        <ProfileField label="Learning Scope" value={profile?.profile?.learning_scope || "Not set"} />
        <ProfileField label="Learning Style" value={profile?.profile?.learning_style || "Not set"} />
        <ProfileField label="Interest Areas" value={
          profile?.profile?.interest_areas?.length > 0
            ? <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                {profile.profile.interest_areas.map((s) => <Chip key={s} label={s} size="small" />)}
              </Box>
            : "Not set"
        } />
      </Paper>

      <ProfileWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSave={handleSave}
        initialProfile={profile?.profile}
      />
    </Box>
  );
}

function ProfileField({ label, value }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", py: 1.5, borderBottom: "1px solid #f0f0f0", "&:last-child": { borderBottom: "none" } }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2" fontWeight={500} component="div">{value}</Typography>
    </Box>
  );
}
