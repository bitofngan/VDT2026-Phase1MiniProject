import { APIProvider } from "@vis.gl/react-google-maps";
import StationMap from "./components/StationMap";

export default function App() {
  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
      <StationMap />
    </APIProvider>
  );
}