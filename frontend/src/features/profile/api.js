import client from "../../api/client";

export async function getProfile() {
  const res = await client.get("/users/profile");
  return res.data;
}

export async function updateProfile(data) {
  const res = await client.put("/users/profile", data);
  return res.data;
}
