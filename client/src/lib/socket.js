import { io } from "socket.io-client";
import { API_URL } from "./api";

export const socket = io(API_URL, {
  autoConnect: false,
  transports: ["websocket", "polling"],
  auth: {
    token: typeof window !== "undefined" ? localStorage.getItem("zoet_token") : undefined
  }
});
