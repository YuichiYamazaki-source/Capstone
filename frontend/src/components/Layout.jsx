import { Outlet, useLocation } from "react-router-dom";
import Box from "@mui/material/Box";
import Navbar from "./Navbar";
import Footer from "./Footer";

const NO_FOOTER_PATHS = ["/explore", "/login", "/onboarding"];

export default function Layout() {
  const location = useLocation();
  const showFooter = !NO_FOOTER_PATHS.includes(location.pathname);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", bgcolor: "background.default" }}>
      <Navbar />
      <Box sx={{ flex: 1 }}>
        <Outlet />
      </Box>
      {showFooter && <Footer />}
    </Box>
  );
}
