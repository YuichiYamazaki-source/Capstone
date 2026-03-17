import client from "../../api/client";

export async function getCourses(params = {}) {
  const res = await client.get("/courses", { params });
  return res.data;
}

export async function searchCourses(params = {}) {
  const res = await client.get("/courses/search", { params });
  return res.data;
}

export async function getFilterOptions() {
  const res = await client.get("/filters/options");
  return res.data;
}
