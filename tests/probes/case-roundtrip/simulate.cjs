// Converter-only simulation of a Case Designer load + save: disk -> in-memory -> disk,
// with the designer's own vendored @uipath/case-schema. No FE rendering, no validation.
const fs = require("fs");
const cs = require(process.env.CS);
const [, , inPath, outPath] = process.argv;
const disk = JSON.parse(fs.readFileSync(inPath, "utf8"));
const mem = cs.transformCaseDiskJsonToInMemoryJson(disk);
const back = cs.transformCaseInMemoryJsonToDiskJson(mem);
fs.writeFileSync(outPath, JSON.stringify(back, null, 2) + "\n");
console.log("ok", Object.keys(back).join(","));
