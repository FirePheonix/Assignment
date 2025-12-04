"use client";

import { AlertCircle, ExternalLink, Copy, Check } from "lucide-react";
import { useState } from "react";

interface InstagramSetupGuideProps {
  onDismiss?: () => void;
}

export function InstagramSetupGuide({ onDismiss }: InstagramSetupGuideProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const redirectUri = "https://gemnar.com/api/instagram/oauth-callback/";
  const localRedirectUri = "http://localhost:8000/api/instagram/oauth-callback/";

  return (
    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-yellow-400 mb-2">Instagram OAuth Setup Required</h3>
          <p className="text-sm text-gray-300 mb-4">
            To connect Instagram accounts, you need to configure a Facebook App for Instagram Basic Display API.
          </p>

          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-medium text-white mb-2">Step 1: Create Facebook App</h4>
              <ol className="space-y-1 text-gray-300 list-decimal list-inside ml-4">
                <li>Go to <a href="https://developers.facebook.com/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">Facebook Developers</a></li>
                <li>Click "Create App" → "Consumer" → "Next"</li>
                <li>Enter app name (e.g., "Gemnar Instagram") and contact email</li>
                <li>Add "Instagram Basic Display" product to your app</li>
              </ol>
            </div>

            <div>
              <h4 className="font-medium text-white mb-2">Step 2: Configure Instagram Basic Display</h4>
              <div className="bg-black/20 rounded p-3 space-y-2">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Valid OAuth Redirect URIs:</label>
                  <div className="flex items-center gap-2">
                    <code className="bg-black/40 px-2 py-1 rounded text-xs flex-1">{redirectUri}</code>
                    <button
                      onClick={() => copyToClipboard(redirectUri, "redirect")}
                      className="p-1 hover:bg-white/10 rounded"
                      title="Copy to clipboard"
                    >
                      {copiedField === "redirect" ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs text-gray-400 mb-1">For Local Development:</label>
                  <div className="flex items-center gap-2">
                    <code className="bg-black/40 px-2 py-1 rounded text-xs flex-1">{localRedirectUri}</code>
                    <button
                      onClick={() => copyToClipboard(localRedirectUri, "local")}
                      className="p-1 hover:bg-white/10 rounded"
                      title="Copy to clipboard"
                    >
                      {copiedField === "local" ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-white mb-2">Step 3: Get App Credentials</h4>
              <p className="text-gray-300 mb-2">From your Facebook App → Settings → Basic:</p>
              <ul className="space-y-1 text-gray-300 list-disc list-inside ml-4">
                <li>Copy the <strong>App ID</strong></li>
                <li>Copy the <strong>App Secret</strong> (show/copy)</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-white mb-2">Step 4: Set Environment Variables</h4>
              <p className="text-gray-300 mb-2">Add these to your Django environment:</p>
              <div className="bg-black/20 rounded p-3">
                <code className="text-xs text-green-400">
                  INSTAGRAM_APP_ID=your_facebook_app_id<br />
                  INSTAGRAM_APP_SECRET=your_facebook_app_secret<br />
                  INSTAGRAM_REDIRECT_URI=https://gemnar.com/api/instagram/oauth-callback/
                </code>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-white mb-2">Step 5: Test</h4>
              <p className="text-gray-300">
                Add yourself as an Instagram Tester in Facebook App → Instagram Basic Display → User Token Generator.
                Then restart your Django server and try connecting again.
              </p>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <a
              href="https://developers.facebook.com/docs/instagram-basic-display-api/getting-started"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors inline-flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Official Documentation
            </a>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
              >
                I'll Set This Up Later
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}