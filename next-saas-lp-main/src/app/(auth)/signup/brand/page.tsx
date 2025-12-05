"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

export default function BrandSignupPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [brandName, setbrandName] = useState("");
  const [website, setWebsite] = useState("");
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const authToken = localStorage.getItem('auth_token');

      // Use the new brand registration API endpoint
      const response = await fetch(`${DJANGO_BACKEND}/api/auth/register/brand/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { 'Authorization': `Token ${authToken}` }),
        },
        body: JSON.stringify({
          email: email,
          password1: password,
          password2: password,
          brand_name: brandName,
          website: website,
        }),
      });

      console.log('Brand signup response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Brand signup success:', data);
        // Registration successful, redirect to dashboard
        router.push('/dashboard');
        router.refresh();
      } else {
        const data = await response.json().catch(() => ({ detail: 'Signup failed' }));
        console.log('Brand signup error:', data);
        
        // Handle various error formats
        let errorMessage = 'Signup failed. Please try again.';
        if (data.email) {
          errorMessage = `Email: ${data.email[0]}`;
        } else if (data.brand_name) {
          errorMessage = `Brand name: ${data.brand_name[0]}`;
        } else if (data.password1) {
          errorMessage = `Password: ${data.password1[0]}`;
        } else if (data.detail) {
          errorMessage = data.detail;
        }
        
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Brand signup exception:', err);
      setError('Connection error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex">
      {/* Left Side - Signup Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Logo & Back */}
          <div className="mb-8">
            <Link href="/signup" className="text-purple-400 hover:text-purple-300 text-sm mb-4 inline-block">
              ← Back to account types
            </Link>
            <h1 className="text-4xl font-bold mb-2">Brand Account</h1>
            <p className="text-gray-400">Create your brand account</p>
          </div>

          {/* Signup Form */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Brand Name */}
              <div>
                <label
                  htmlFor="brandName"
                  className="block text-sm font-medium mb-2"
                >
                  Brand Name
                </label>
                <input
                  id="brandName"
                  type="text"
                  required
                  value={brandName}
                  onChange={(e) => setbrandName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Acme Inc."
                />
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium mb-2"
                >
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="contact@acme.com"
                />
              </div>

              {/* Website */}
              <div>
                <label
                  htmlFor="website"
                  className="block text-sm font-medium mb-2"
                >
                  Website URL (Optional)
                </label>
                <input
                  id="website"
                  type="url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="https://acme.com"
                />
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium mb-2"
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  At least 8 characters with uppercase, lowercase, and numbers
                </p>
              </div>

              {/* Terms */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreeToTerms}
                  onChange={(e) => setAgreeToTerms(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded border-white/10 bg-white/5 text-purple-500 focus:ring-purple-500"
                  required
                />
                <span className="text-sm text-gray-400">
                  I agree to the{" "}
                  <Link href="/terms" className="text-purple-400 hover:text-purple-300">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" className="text-purple-400 hover:text-purple-300">
                    Privacy Policy
                  </Link>
                </span>
              </label>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white font-medium py-3 px-4 rounded-lg transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Creating account..." : "Create Brand Account"}
              </button>
            </form>

            {/* Login Link */}
            <p className="mt-6 text-center text-sm text-gray-400">
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
      </div>

      {/* Right Side - Mockup Image */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-8 bg-gradient-to-br from-purple-900/20 to-pink-900/20">
        <div className="relative w-full max-w-2xl aspect-square">
          <Image
            src="/images/signup-brand.png"
            alt="Brand Platform"
            fill
            className="object-contain"
            priority
          />
        </div>
      </div>
    </div>
  );
}
