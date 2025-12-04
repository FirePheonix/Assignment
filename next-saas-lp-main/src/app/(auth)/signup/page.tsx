"use client";

import Link from "next/link";
import Image from "next/image";
import { Building2, Sparkles } from "lucide-react";

export default function SignupChoicePage() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-8">
      <div className="w-full max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4">GEMNAR</h1>
          <p className="text-xl text-gray-400">Choose your account type</p>
        </div>

        {/* Two Column Selection */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Brand/Business Account */}
          <Link
            href="/signup/brand"
            className="group bg-white/5 border border-white/10 hover:border-purple-500/50 rounded-3xl p-8 transition-all hover:scale-105"
          >
            <div className="flex flex-col items-center text-center">
              {/* Icon */}
              <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Building2 className="w-10 h-10" />
              </div>

              {/* Title */}
              <h2 className="text-3xl font-bold mb-3">Brand Account</h2>
              <p className="text-gray-400 mb-6">
                For businesses, brands, and organizations looking to create and
                manage AI-generated content at scale
              </p>

              {/* Features */}
              <ul className="space-y-2 text-left w-full mb-8">
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                  Team collaboration tools
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                  Advanced analytics
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                  API access
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                  White-label options
                </li>
              </ul>

              {/* Image */}
              <div className="relative w-full aspect-video rounded-xl overflow-hidden">
                <Image
                  src="/images/signup-brand.png"
                  alt="Brand Account"
                  fill
                  className="object-cover"
                />
              </div>

              {/* CTA */}
              <div className="mt-6 w-full py-3 px-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-medium text-center group-hover:opacity-90 transition-opacity">
                Sign up as Brand
              </div>
            </div>
          </Link>

          {/* Creator Account */}
          <Link
            href="/signup/creator"
            className="group bg-white/5 border border-white/10 hover:border-pink-500/50 rounded-3xl p-8 transition-all hover:scale-105"
          >
            <div className="flex flex-col items-center text-center">
              {/* Icon */}
              <div className="w-20 h-20 bg-gradient-to-br from-pink-500 to-orange-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Sparkles className="w-10 h-10" />
              </div>

              {/* Title */}
              <h2 className="text-3xl font-bold mb-3">Creator Account</h2>
              <p className="text-gray-400 mb-6">
                For artists, designers, and content creators who want to
                explore AI-powered creative tools
              </p>

              {/* Features */}
              <ul className="space-y-2 text-left w-full mb-8">
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                  Personal portfolio
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                  AI workflow builder
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                  Community features
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                  Free tier available
                </li>
              </ul>

              {/* Image */}
              <div className="relative w-full aspect-video rounded-xl overflow-hidden">
                <Image
                  src="/images/signup-artist.png"
                  alt="Creator Account"
                  fill
                  className="object-cover"
                />
              </div>

              {/* CTA */}
              <div className="mt-6 w-full py-3 px-6 bg-gradient-to-r from-pink-500 to-orange-500 rounded-lg font-medium text-center group-hover:opacity-90 transition-opacity">
                Sign up as Creator
              </div>
            </div>
          </Link>
        </div>

        {/* Login Link */}
        <p className="mt-12 text-center text-sm text-gray-400">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-purple-400 hover:text-purple-300 font-medium"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
