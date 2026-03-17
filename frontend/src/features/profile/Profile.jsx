import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import { useAuth } from "../../contexts/AuthContext";
import { getProfile, updateProfile } from "./api";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
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

  const startEdit = () => {
    setEditData({
      skills: profile?.profile?.skills?.join(", ") || "",
      motivation: profile?.profile?.motivation || "",
      learning_scope: profile?.profile?.learning_scope || "",
      learning_style: profile?.profile?.learning_style || "",
      interest_areas: profile?.profile?.interest_areas?.join(", ") || "",
    });
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      const payload = {
        skills: editData.skills ? editData.skills.split(",").map((s) => s.trim()).filter(Boolean) : [],
        motivation: editData.motivation || null,
        learning_scope: editData.learning_scope || null,
        learning_style: editData.learning_style || null,
        interest_areas: editData.interest_areas ? editData.interest_areas.split(",").map((s) => s.trim()).filter(Boolean) : [],
      };
      const data = await updateProfile(payload);
      setProfile(data);
      updateUser({ ...user, profile: data.profile });
      setEditing(false);
      setMessage("Profile updated!");
    } catch {
      setMessage("Failed to update profile");
    } finally {
      setSaving(false);
    }
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
          {!editing && (
            <Button size="small" onClick={startEdit}>
              Edit
            </Button>
          )}
        </Box>

        {editing ? (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Skills (comma-separated)"
              value={editData.skills}
              onChange={(e) => setEditData({ ...editData, skills: e.target.value })}
              fullWidth
            />
            <TextField
              label="Motivation"
              value={editData.motivation}
              onChange={(e) => setEditData({ ...editData, motivation: e.target.value })}
              fullWidth
            />
            <TextField
              label="Learning Scope"
              value={editData.learning_scope}
              onChange={(e) => setEditData({ ...editData, learning_scope: e.target.value })}
              fullWidth
            />
            <TextField
              label="Learning Style"
              value={editData.learning_style}
              onChange={(e) => setEditData({ ...editData, learning_style: e.target.value })}
              fullWidth
            />
            <TextField
              label="Interest Areas (comma-separated)"
              value={editData.interest_areas}
              onChange={(e) => setEditData({ ...editData, interest_areas: e.target.value })}
              fullWidth
            />
            <Box sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
              <Button onClick={() => setEditing(false)}>Cancel</Button>
              <Button variant="contained" onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
            </Box>
          </Box>
        ) : (
          <>
            <ProfileField label="Skills" value={
              profile?.profile?.skills?.length > 0
                ? <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                    {profile.profile.skills.map((s) => <Chip key={s} label={s} size="small" />)}
                  </Box>
                : "Not set"
            } />
            <ProfileField label="Motivation" value={profile?.profile?.motivation || "Not set"} />
            <ProfileField label="Learning Scope" value={profile?.profile?.learning_scope || "Not set"} />
            <ProfileField label="Learning Style" value={profile?.profile?.learning_style || "Not set"} />
            <ProfileField label="Interest Areas" value={
              profile?.profile?.interest_areas?.length > 0
                ? profile.profile.interest_areas.join(", ")
                : "Not set"
            } />
          </>
        )}
      </Paper>
    </Box>
  );
}

function ProfileField({ label, value }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", py: 1.5, borderBottom: "1px solid #f0f0f0", "&:last-child": { borderBottom: "none" } }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2" fontWeight={500}>{value}</Typography>
    </Box>
  );
}
