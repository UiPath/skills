import { UiPath } from "@uipath/uipath-typescript";

const sdk = new UiPath();

export async function loadDepots(): Promise<string[]> {
  const rows = await sdk.entities.getAllRecords("Depot");
  return rows.items.map((r) => String(r.Name));
}
