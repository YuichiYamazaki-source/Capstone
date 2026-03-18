import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import InputBase from "@mui/material/InputBase";
import Pagination from "@mui/material/Pagination";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import SearchIcon from "@mui/icons-material/Search";
import CourseCard from "./CourseCard";
import { getCourses, searchCourses, getFilterOptions } from "./api";
import { useAuth } from "../../contexts/AuthContext";

const TRENDING_TOPICS = [
  { label: "Machine Learning", query: "machine learning" },
  { label: "Python", query: "python" },
  { label: "Data Analysis", query: "data analysis" },
  { label: "Cloud Computing", query: "cloud" },
  { label: "Cybersecurity", query: "cybersecurity" },
  { label: "AI & Deep Learning", query: "deep learning" },
  { label: "Project Management", query: "project management" },
  { label: "Marketing", query: "marketing" },
];

const PAGE_SIZE = 12;

function scoreMatch(course, profile) {
  if (!profile?.skills?.length) return { score: 0, reasons: [] };

  let score = 0;
  const reasons = [];
  const userSkills = profile.skills.map((s) => (typeof s === "string" ? s : s.name).toLowerCase());
  const courseSkills = (course.skills || []).map((s) => s.toLowerCase());

  const overlap = courseSkills.filter((s) =>
    userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  if (overlap.length > 0) {
    score += overlap.length * 2;
    reasons.push(`Matches your skills: ${overlap.join(", ")}`);
  }

  const newSkills = courseSkills.filter(
    (s) => !userSkills.some((us) => s.includes(us) || us.includes(s))
  );
  if (newSkills.length > 0) {
    score += newSkills.length;
    reasons.push(`New skills to learn: ${newSkills.join(", ")}`);
  }

  if (course.rating && course.rating >= 4.5) {
    score += 1;
    reasons.push("Highly rated course");
  }

  if (profile.motivation === "Career Change" && course.level === "Beginner") {
    score += 2;
    reasons.push("Good for career changers");
  }
  if (profile.motivation === "Skill Up at Current Job" && course.level === "Intermediate") {
    score += 2;
    reasons.push("Great for upskilling");
  }

  return { score, reasons };
}

export default function Search() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [courses, setCourses] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ level: "", organization: "", skills: [] });
  const [filterOptions, setFilterOptions] = useState({ levels: [], organizations: [], skills: [] });
  const [loading, setLoading] = useState(false);
  const [activeQuery, setActiveQuery] = useState("");
  const [activeTopic, setActiveTopic] = useState("");
  const [filterSearch, setFilterSearch] = useState("");
  const [orgSearch, setOrgSearch] = useState("");

  const profile = user?.profile;
  const hasProfile = profile?.skills?.length > 0 && profile?.motivation;

  useEffect(() => {
    getFilterOptions().then(setFilterOptions).catch(() => {});
  }, []);

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      setActiveQuery(q);
      setActiveTopic("");
      setPage(1);
      performSearch(q, 0);
    } else {
      setActiveQuery("");
      loadCourses({ offset: 0 });
    }
  }, [searchParams]);

  const loadCourses = async (overrides = {}) => {
    setLoading(true);
    try {
      const { level, organization, skills, ...rest } = {
        limit: PAGE_SIZE,
        offset: 0,
        ...filters,
        ...overrides,
      };
      const params = {
        ...rest,
        ...(level ? { level } : {}),
        ...(organization ? { organization } : {}),
        ...(skills?.length ? { skills } : {}),
      };
      const data = await getCourses(params);
      setCourses(data.courses);
      setTotal(data.total);
    } catch {
      setCourses([]);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async (q, offset = 0) => {
    setLoading(true);
    try {
      const data = await searchCourses({ q, limit: PAGE_SIZE, offset });
      setCourses(data.courses);
      setTotal(data.total);
    } catch {
      setCourses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = (topic) => {
    if (activeTopic === topic.label) {
      setActiveTopic("");
      setActiveQuery("");
      setPage(1);
      loadCourses({ offset: 0 });
    } else {
      setActiveTopic(topic.label);
      setActiveQuery(topic.query);
      setPage(1);
      performSearch(topic.query, 0);
    }
  };

  const handleFilterClick = (type, value) => {
    const newFilters = { ...filters };
    if (type === "skills") {
      const idx = newFilters.skills.indexOf(value);
      if (idx >= 0) {
        newFilters.skills = newFilters.skills.filter((s) => s !== value);
      } else {
        newFilters.skills = [...newFilters.skills, value];
      }
    } else {
      newFilters[type] = newFilters[type] === value ? "" : value;
    }
    setFilters(newFilters);
    setActiveQuery("");
    setActiveTopic("");
    setPage(1);
    loadCourses({ ...newFilters, offset: 0 });
  };

  const handlePageChange = (_, newPage) => {
    setPage(newPage);
    const offset = (newPage - 1) * PAGE_SIZE;
    if (activeQuery) {
      performSearch(activeQuery, offset);
    } else {
      loadCourses({ offset });
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Compute recommendation reasons for each course
  const coursesWithReasons = useMemo(() => {
    if (!hasProfile) return courses.map((c) => ({ ...c, reasons: [] }));
    return courses.map((c) => {
      const { reasons } = scoreMatch(c, profile);
      return { ...c, reasons };
    });
  }, [courses, hasProfile, profile]);

  // Filtered organizations for the filter panel search
  const filteredOrgs = useMemo(() => {
    const allOrgs = filterOptions.organizations || [];
    if (!orgSearch.trim()) return allOrgs;
    const q = orgSearch.toLowerCase();
    return allOrgs.filter((o) => o.toLowerCase().includes(q));
  }, [filterOptions.organizations, orgSearch]);

  // Filtered skills for the filter panel search
  const filteredSkills = useMemo(() => {
    const allSkills = filterOptions.skills || [];
    if (!filterSearch.trim()) return allSkills;
    const q = filterSearch.toLowerCase();
    return allSkills.filter((s) => s.toLowerCase().includes(q));
  }, [filterOptions.skills, filterSearch]);

  return (
    <Box sx={{ px: { xs: 2, md: 6, lg: 10 }, py: 3 }}>
      {/* Trending topics bar */}
      <Paper
        sx={{
          p: 2,
          mb: 2.5,
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          flexWrap: "wrap",
        }}
        elevation={0}
        variant="outlined"
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mr: 1, flexShrink: 0 }}>
          <TrendingUpIcon sx={{ fontSize: 18, color: "#6c63ff" }} />
          <Typography variant="subtitle2" fontWeight={600} fontSize={13} color="text.secondary">
            Trending
          </Typography>
        </Box>
        {TRENDING_TOPICS.map((topic) => (
          <Chip
            key={topic.label}
            label={topic.label}
            size="small"
            variant={activeTopic === topic.label ? "filled" : "outlined"}
            color={activeTopic === topic.label ? "primary" : "default"}
            onClick={() => handleTopicClick(topic)}
            sx={{ fontSize: 12, cursor: "pointer" }}
          />
        ))}
      </Paper>

      {/* Title + count */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        <Typography variant="h6" fontWeight={700}>
          {activeQuery ? `Results for "${activeQuery}"` : "Browse Courses"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          ({total} found)
        </Typography>
      </Box>

      <Box sx={{ display: "flex", gap: 2.5 }}>
        {/* Filter Panel */}
        <Paper sx={{ width: 240, flexShrink: 0, p: 2, height: "fit-content", position: "sticky", top: 68 }}>
          <Typography variant="subtitle2" fontWeight={600} mb={1.5} fontSize={13}>
            Filters
          </Typography>

          {/* Level filter */}
          <Box mb={2}>
            <Typography variant="caption" color="text.secondary" fontWeight={600}>Level</Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
              {filterOptions.levels.map((lvl) => (
                <Chip
                  key={lvl} label={lvl} size="small"
                  variant={filters.level === lvl ? "filled" : "outlined"}
                  color={filters.level === lvl ? "primary" : "default"}
                  onClick={() => handleFilterClick("level", lvl)}
                  sx={{ fontSize: 11 }}
                />
              ))}
            </Box>
          </Box>

          {/* Organization filter with search */}
          <Box mb={2}>
            <Typography variant="caption" color="text.secondary" fontWeight={600}>Organization</Typography>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                border: "1px solid #ddd",
                borderRadius: 1,
                px: 1,
                py: 0.25,
                mt: 0.5,
                mb: 1,
                "&:focus-within": { borderColor: "#6c63ff" },
              }}
            >
              <SearchIcon sx={{ fontSize: 16, color: "#999", mr: 0.5 }} />
              <InputBase
                placeholder="Search organizations..."
                value={orgSearch}
                onChange={(e) => setOrgSearch(e.target.value)}
                sx={{ fontSize: 12, flex: 1 }}
              />
            </Box>

            {/* Selected organization */}
            {filters.organization && (
              <Box sx={{ mb: 1 }}>
                <Chip
                  label={filters.organization} size="small"
                  color="primary"
                  onDelete={() => handleFilterClick("organization", filters.organization)}
                  sx={{ fontSize: 10 }}
                />
              </Box>
            )}

            <Box sx={{ maxHeight: 200, overflowY: "auto", display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {filteredOrgs
                .filter((o) => o !== filters.organization)
                .map((org) => (
                  <Chip
                    key={org} label={org} size="small"
                    variant="outlined"
                    onClick={() => handleFilterClick("organization", org)}
                    sx={{ fontSize: 10, cursor: "pointer" }}
                  />
                ))}
              {filteredOrgs.length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ py: 1 }}>
                  No organizations match &quot;{orgSearch}&quot;
                </Typography>
              )}
            </Box>
          </Box>

          {/* Skills filter with search */}
          <Box>
            <Typography variant="caption" color="text.secondary" fontWeight={600}>Skills</Typography>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                border: "1px solid #ddd",
                borderRadius: 1,
                px: 1,
                py: 0.25,
                mt: 0.5,
                mb: 1,
                "&:focus-within": { borderColor: "#6c63ff" },
              }}
            >
              <SearchIcon sx={{ fontSize: 16, color: "#999", mr: 0.5 }} />
              <InputBase
                placeholder="Search skills..."
                value={filterSearch}
                onChange={(e) => setFilterSearch(e.target.value)}
                sx={{ fontSize: 12, flex: 1 }}
              />
            </Box>

            {/* Selected skills (always visible at top) */}
            {filters.skills.length > 0 && (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 1 }}>
                {filters.skills.map((s) => (
                  <Chip
                    key={s} label={s} size="small"
                    color="primary"
                    onDelete={() => handleFilterClick("skills", s)}
                    sx={{ fontSize: 10 }}
                  />
                ))}
              </Box>
            )}

            {/* Scrollable skill list */}
            <Box sx={{ maxHeight: 280, overflowY: "auto", display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {filteredSkills
                .filter((s) => !filters.skills.includes(s))
                .map((s) => (
                  <Chip
                    key={s} label={s} size="small"
                    variant="outlined"
                    onClick={() => handleFilterClick("skills", s)}
                    sx={{ fontSize: 10, cursor: "pointer" }}
                  />
                ))}
              {filteredSkills.length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ py: 1 }}>
                  No skills match &quot;{filterSearch}&quot;
                </Typography>
              )}
            </Box>
          </Box>
        </Paper>

        {/* Results Grid */}
        <Box sx={{ flex: 1 }}>
          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
              <CircularProgress />
            </Box>
          ) : courses.length === 0 ? (
            <Typography color="text.secondary" textAlign="center" py={8}>
              No courses found. Try a different search or filter.
            </Typography>
          ) : (
            <>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", lg: "1fr 1fr 1fr" },
                  gap: 2,
                }}
              >
                {coursesWithReasons.map((course) => (
                  <CourseCard key={course.id} course={course} reasons={course.reasons} />
                ))}
              </Box>

              {/* Pagination */}
              {totalPages > 1 && (
                <Box sx={{ display: "flex", justifyContent: "center", mt: 3, mb: 1 }}>
                  <Pagination
                    count={totalPages}
                    page={page}
                    onChange={handlePageChange}
                    color="primary"
                    shape="rounded"
                  />
                </Box>
              )}
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
}
