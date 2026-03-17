import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Avatar from "@mui/material/Avatar";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import Divider from "@mui/material/Divider";
import InputBase from "@mui/material/InputBase";
import IconButton from "@mui/material/IconButton";
import SchoolIcon from "@mui/icons-material/School";
import PersonIcon from "@mui/icons-material/Person";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsIcon from "@mui/icons-material/Settings";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import SearchIcon from "@mui/icons-material/Search";
import NotificationsNoneIcon from "@mui/icons-material/NotificationsNone";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const handleLogout = () => {
    setAnchorEl(null);
    logout();
    navigate("/login");
  };

  const handleSearch = (e) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery("");
    }
  };

  const navBtn = (label, path) => (
    <Button
      key={path}
      onClick={() => navigate(path)}
      sx={{
        color: location.pathname === path ? "#fff" : "rgba(255,255,255,0.75)",
        fontSize: 13,
        fontWeight: 500,
        px: 1.5,
        py: 0.5,
        minWidth: "auto",
        whiteSpace: "nowrap",
        "&:hover": { color: "#fff", bgcolor: "transparent" },
      }}
    >
      {label}
    </Button>
  );

  return (
    <AppBar position="sticky" sx={{ bgcolor: "#1a1a2e" }} elevation={0}>
      <Toolbar sx={{ minHeight: 52, px: { xs: 1.5, md: 2.5 }, gap: 0.5 }}>
        {/* Logo */}
        <Box
          sx={{ display: "flex", alignItems: "center", gap: 0.75, cursor: "pointer", flexShrink: 0, mr: 1 }}
          onClick={() => navigate("/")}
        >
          <SchoolIcon sx={{ fontSize: 22 }} />
          <Typography fontWeight={700} fontSize={16} sx={{ display: { xs: "none", sm: "block" } }}>
            Course Finder
          </Typography>
        </Box>

        {/* Left nav */}
        {navBtn("Explore", "/explore")}
        {navBtn("Browse", "/search")}

        {/* Search bar — Udemy style: wide, bordered, rounded */}
        <Box
          sx={{
            flex: 1,
            mx: 1.5,
            display: "flex",
            alignItems: "center",
            border: "1px solid rgba(255,255,255,0.3)",
            borderRadius: 50,
            px: 2,
            height: 40,
            bgcolor: "transparent",
            transition: "all 0.2s",
            "&:focus-within": {
              borderColor: "#fff",
              bgcolor: "rgba(255,255,255,0.05)",
            },
          }}
        >
          <SearchIcon sx={{ color: "rgba(255,255,255,0.5)", fontSize: 20, mr: 1 }} />
          <InputBase
            placeholder="Search courses, skills, topics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
            fullWidth
            sx={{
              color: "#fff",
              fontSize: 14,
              "& ::placeholder": { color: "rgba(255,255,255,0.45)", opacity: 1 },
            }}
          />
        </Box>

        {/* Right nav */}
        {user && navBtn("Personal Analysis", "/analysis")}
        {user && navBtn("My Learning", "/")}

        {/* Icons + User */}
        {user ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, ml: 0.5 }}>
            <IconButton size="small" sx={{ color: "rgba(255,255,255,0.7)" }}>
              <NotificationsNoneIcon sx={{ fontSize: 20 }} />
            </IconButton>
            <Box
              onClick={(e) => setAnchorEl(e.currentTarget)}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                p: 0.5,
                borderRadius: 2,
                "&:hover": { bgcolor: "rgba(255,255,255,0.1)" },
              }}
            >
              <Avatar sx={{ width: 30, height: 30, bgcolor: "#6c63ff", fontSize: 14 }}>
                {user.name?.[0]?.toUpperCase() || "U"}
              </Avatar>
            </Box>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={() => setAnchorEl(null)}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              slotProps={{ paper: { sx: { mt: 0.5, minWidth: 200 } } }}
            >
              <Box sx={{ px: 2, py: 1.5, borderBottom: "1px solid #eee" }}>
                <Typography variant="subtitle2" fontWeight={600}>{user.name}</Typography>
                <Typography variant="caption" color="text.secondary">{user.email}</Typography>
              </Box>
              <MenuItem onClick={() => { setAnchorEl(null); navigate("/profile"); }}>
                <ListItemIcon><PersonIcon fontSize="small" /></ListItemIcon>
                Profile
              </MenuItem>
              <MenuItem onClick={() => { setAnchorEl(null); navigate("/analysis"); }}>
                <ListItemIcon><AnalyticsIcon fontSize="small" /></ListItemIcon>
                My Analysis
              </MenuItem>
              <MenuItem onClick={() => { setAnchorEl(null); navigate("/onboarding"); }}>
                <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                Edit Preferences
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
                Logout
              </MenuItem>
            </Menu>
          </Box>
        ) : (
          <Box sx={{ display: "flex", gap: 1, ml: 1 }}>
            <Button
              size="small"
              onClick={() => navigate("/login")}
              sx={{
                color: "#fff",
                border: "1px solid rgba(255,255,255,0.4)",
                fontSize: 13,
                px: 2,
                "&:hover": { borderColor: "#fff" },
              }}
            >
              Log in
            </Button>
            <Button
              size="small"
              onClick={() => navigate("/login")}
              sx={{
                color: "#1a1a2e",
                bgcolor: "#fff",
                fontSize: 13,
                px: 2,
                "&:hover": { bgcolor: "rgba(255,255,255,0.9)" },
              }}
            >
              Sign up
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
