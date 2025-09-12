import { jwtDecode } from "jwt-decode";
import { ACCESS_TOKEN } from "./constants";

export function getCurrentUsername() {
  const token = localStorage.getItem(ACCESS_TOKEN);
  if (!token) return null;
  try {
    const decoded = jwtDecode(token);
    const fromToken = decoded?.username
      || decoded?.user?.username
      || decoded?.name
      || decoded?.preferred_username
      || decoded?.sub;
    return fromToken ? String(fromToken) : null;
  } catch (_e) {
    return null;
  }
}


