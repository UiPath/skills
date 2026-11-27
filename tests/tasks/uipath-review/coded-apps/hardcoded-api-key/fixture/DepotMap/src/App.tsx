import React, { useEffect, useState } from "react";
import { loadDepots } from "./api/client";

export function App() {
  const [depots, setDepots] = useState<string[]>([]);
  useEffect(() => { loadDepots().then(setDepots); }, []);
  return <ul>{depots.map((d) => <li key={d}>{d}</li>)}</ul>;
}
