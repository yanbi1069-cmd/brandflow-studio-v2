import { spawn } from "node:child_process";

const windows = process.platform === "win32";
const children = [
  spawn(windows ? "python" : "python3", ["local-agent/app.py"], { stdio: "inherit", shell: windows }),
  spawn(windows ? "npm.cmd" : "npm", ["run", "dev"], { stdio: "inherit", shell: windows }),
];

let closing = false;
function close(code = 0) {
  if (closing) return;
  closing = true;
  for (const child of children) if (!child.killed) child.kill();
  setTimeout(() => process.exit(code), 200);
}

for (const child of children) {
  child.on("exit", (code) => { if (!closing && code) close(code); });
  child.on("error", () => close(1));
}
process.on("SIGINT", () => close(0));
process.on("SIGTERM", () => close(0));
