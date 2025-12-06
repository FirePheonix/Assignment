const path = require('path');
const webpack = require('webpack');

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
  webpack: (config, { isServer }) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './src'),
    };
    config.resolve.extensions = [
      '.ts',
      '.tsx',
      '.js',
      '.jsx',
      '.json',
      ...config.resolve.extensions,
    ];
    
    // Fix for esbuild __name helper not defined in production
    // This polyfill is needed for packages bundled with esbuild's keepNames option
    // (like @ai-sdk/react and ai packages)
    config.plugins.push(
      new webpack.ProvidePlugin({
        __name: [path.resolve(__dirname, './src/lib/esbuild-shim.js'), '__name'],
      })
    );
    
    return config;
  },
};

module.exports = nextConfig;
