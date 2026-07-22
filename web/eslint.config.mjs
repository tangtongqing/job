import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  {
    rules: {
      // Existing client hydration and API-loading effects intentionally update
      // local state after mount; keeping them preserves the verified UX.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  globalIgnores([".next/**", "dist/**", ".vinext/**", "next-env.d.ts"]),
]);
