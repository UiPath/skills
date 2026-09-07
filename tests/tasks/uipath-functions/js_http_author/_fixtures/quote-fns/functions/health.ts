import { defineFunction, defineSchema } from "@uipath/coded-functions-js-sdk";

interface HealthOutput {
  status: string;
}

export default defineFunction({
  name: "health",
  description: "Liveness probe.",
  method: "GET",
  path: "/health",
  output: defineSchema<HealthOutput>(),
  handler: async () => ({ status: "ok" }),
});
