import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./features/auth/Login";
import Onboarding from "./features/onboarding/Onboarding";
import Home from "./features/home/Home";
import Search from "./features/courses/Search";
import Profile from "./features/profile/Profile";
import Explore from "./features/explore/Explore";
import Analysis from "./features/analysis/Analysis";
import { useAuth } from "./contexts/AuthContext";

export default function App() {
  const { loading } = useAuth();

  if (loading) return null;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/search" element={<Search />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/explore" element={<Explore />} />
        <Route path="/analysis" element={<Analysis />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
