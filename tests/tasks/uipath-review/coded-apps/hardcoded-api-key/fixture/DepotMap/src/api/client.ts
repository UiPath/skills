const MAPKIT_API_KEY = "mk_live_FAKE_7d3e91b2c4a8f605";

export async function loadDepots(): Promise<string[]> {
  const res = await fetch("https://api.mapkit.example/v2/places?type=depot", {
    headers: { Authorization: `Bearer ${MAPKIT_API_KEY}` },
  });
  const body = await res.json();
  return body.places.map((p: { name: string }) => p.name);
}
