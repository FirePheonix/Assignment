// Polyfill for esbuild's __name helper
// This is needed for packages bundled with esbuild's keepNames option
// (like @ai-sdk/react and ai packages)

export const __name = (target, value) => {
  return Object.defineProperty(target, "name", { value, configurable: true });
};

