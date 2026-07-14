import nextConfig from "eslint-config-next";

const eslintConfig = [
  ...nextConfig,
  {
    // This project does not opt into the React Compiler, so the compiler-linked
    // preview rules (which flag standard fetch-on-mount effect patterns used
    // throughout the app) are disabled rather than rewriting every data-loading
    // component around them.
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/purity": "off",
      "react-hooks/immutability": "off",
    },
  },
];

export default eslintConfig;
