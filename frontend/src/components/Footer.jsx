import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        bgcolor: "#1a1a2e",
        color: "rgba(255,255,255,0.6)",
        py: 3,
        px: { xs: 2, md: 4 },
        mt: "auto",
      }}
    >
      <Box
        sx={{
          maxWidth: 1200,
          mx: "auto",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Typography variant="body2" fontSize={12}>
          Course Finder — Intelligent University Course Discovery
        </Typography>
        <Box sx={{ display: "flex", gap: 3 }}>
          <Link href="#" underline="hover" color="inherit" fontSize={12}>
            About
          </Link>
          <Link href="#" underline="hover" color="inherit" fontSize={12}>
            Privacy
          </Link>
          <Link href="#" underline="hover" color="inherit" fontSize={12}>
            Contact
          </Link>
        </Box>
      </Box>
    </Box>
  );
}
