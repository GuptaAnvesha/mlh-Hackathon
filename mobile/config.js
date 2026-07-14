// Point this at your running FastAPI backend.
//
// - Web / same machine:            http://localhost:8000
// - Phone on the same Wi-Fi:       http://<YOUR_COMPUTER_LAN_IP>:8000
//   (find it with `ipconfig` on Windows — e.g. http://192.168.1.42:8000)
//
// The phone and your computer must be on the same network, and the backend
// must be started with:  uvicorn veritas.api:app --host 0.0.0.0 --port 8000
export const API_BASE_URL = "https://192.168.1.16";
