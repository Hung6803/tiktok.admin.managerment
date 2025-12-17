'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

/**
 * Privacy Policy page
 * Required for TikTok Developer App Review compliance
 * Compliant with GDPR, CCPA, and TikTok Developer Guidelines
 */
export default function PrivacyPolicyPage() {
  const lastUpdated = 'December 17, 2025'
  const appName = 'TikTok Manager'
  const companyName = 'TikTok Manager'
  const contactEmail = 'privacy@tiktokmanager.app'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <article className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8 md:p-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Privacy Policy
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            Last updated: {lastUpdated}
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-6">
            {/* Introduction */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                1. Introduction
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} ("we," "our," or "us") is committed to protecting your privacy.
                This Privacy Policy explains how we collect, use, disclose, and safeguard your
                information when you use our social media management service that integrates
                with TikTok's API.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                By using {appName}, you consent to the data practices described in this policy.
                If you do not agree with this Privacy Policy, please do not use our service.
              </p>
            </section>

            {/* Information We Collect */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                2. Information We Collect
              </h2>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                2.1 Information You Provide
              </h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li><strong>Account Information:</strong> Email address and password when you create an account</li>
                <li><strong>Content:</strong> Videos, images, and captions you upload for publishing</li>
                <li><strong>Scheduling Data:</strong> Post schedules, privacy preferences, and publishing settings</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                2.2 Information from TikTok
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                When you connect your TikTok account, we receive the following information
                through TikTok's official API (based on your authorization):
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li><strong>Basic Profile:</strong> TikTok username, display name, avatar, and open_id</li>
                <li><strong>Profile Information:</strong> Bio, verification status, and profile links</li>
                <li><strong>Account Statistics:</strong> Follower count, following count, likes, and video count</li>
                <li><strong>OAuth Tokens:</strong> Access and refresh tokens for API authentication</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                2.3 Automatically Collected Information
              </h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li><strong>Usage Data:</strong> Features used, actions taken, and interaction patterns</li>
                <li><strong>Device Information:</strong> Browser type, operating system, and device identifiers</li>
                <li><strong>Log Data:</strong> IP address, access times, and pages viewed</li>
              </ul>
            </section>

            {/* How We Use Your Information */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                3. How We Use Your Information
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We use the collected information for the following purposes:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li><strong>Service Provision:</strong> To provide, maintain, and improve our services</li>
                <li><strong>Content Publishing:</strong> To schedule and publish your content to TikTok</li>
                <li><strong>Analytics:</strong> To display your TikTok account statistics and performance metrics</li>
                <li><strong>Authentication:</strong> To verify your identity and maintain account security</li>
                <li><strong>Communication:</strong> To send service-related notifications and updates</li>
                <li><strong>Support:</strong> To respond to your inquiries and provide customer support</li>
                <li><strong>Compliance:</strong> To comply with legal obligations and enforce our terms</li>
              </ul>
            </section>

            {/* TikTok API Data Usage */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                4. TikTok API Data Usage
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Our use of information received from TikTok APIs adheres to{' '}
                <a
                  href="https://developers.tiktok.com/doc/tiktok-api-v2-terms-of-use"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  TikTok's API Terms of Use
                </a>{' '}
                and{' '}
                <a
                  href="https://www.tiktok.com/legal/page/global/tik-tok-developer-terms-of-service/en"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Developer Terms of Service
                </a>.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Specifically, we:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Only request the minimum scopes necessary for our services</li>
                <li>Do not sell or share TikTok user data with third parties for advertising</li>
                <li>Do not use TikTok data for purposes other than providing our stated services</li>
                <li>Securely store and encrypt all OAuth tokens</li>
                <li>Delete TikTok data when you disconnect your account or request deletion</li>
              </ul>
            </section>

            {/* Data Sharing */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                5. Data Sharing and Disclosure
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We do not sell your personal information. We may share your information in
                the following circumstances:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li><strong>With TikTok:</strong> To publish content and retrieve data through their API</li>
                <li><strong>Service Providers:</strong> With trusted third parties who assist in operating our service (hosting, analytics)</li>
                <li><strong>Legal Requirements:</strong> When required by law, court order, or governmental authority</li>
                <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                <li><strong>Protection:</strong> To protect our rights, privacy, safety, or property</li>
              </ul>
            </section>

            {/* Data Security */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                6. Data Security
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We implement appropriate technical and organizational security measures to protect
                your personal information, including:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Encryption of data in transit (TLS/SSL) and at rest</li>
                <li>Secure storage of OAuth tokens with encryption</li>
                <li>Regular security assessments and updates</li>
                <li>Access controls and authentication mechanisms</li>
                <li>Secure password hashing (bcrypt)</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                However, no method of transmission over the Internet is 100% secure. While we
                strive to protect your data, we cannot guarantee absolute security.
              </p>
            </section>

            {/* Data Retention */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                7. Data Retention
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We retain your information for as long as necessary to provide our services
                and fulfill the purposes outlined in this policy. Specifically:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li><strong>Account Data:</strong> Retained until you delete your account</li>
                <li><strong>Content:</strong> Retained until published or deleted by you</li>
                <li><strong>TikTok Tokens:</strong> Retained while your TikTok account is connected; deleted upon disconnection</li>
                <li><strong>Analytics Data:</strong> Retained for up to 12 months for historical reporting</li>
                <li><strong>Log Data:</strong> Retained for up to 90 days for security and debugging purposes</li>
              </ul>
            </section>

            {/* Your Rights */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                8. Your Rights
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Depending on your location, you may have the following rights regarding your
                personal information:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li><strong>Access:</strong> Request a copy of your personal data</li>
                <li><strong>Correction:</strong> Request correction of inaccurate data</li>
                <li><strong>Deletion:</strong> Request deletion of your personal data</li>
                <li><strong>Portability:</strong> Request transfer of your data to another service</li>
                <li><strong>Objection:</strong> Object to certain processing of your data</li>
                <li><strong>Withdraw Consent:</strong> Withdraw consent at any time where processing is based on consent</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                To exercise these rights, please contact us at{' '}
                <a
                  href={`mailto:${contactEmail}`}
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {contactEmail}
                </a>.
              </p>
            </section>

            {/* Revoking TikTok Access */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                9. Revoking TikTok Access
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You can revoke {appName}'s access to your TikTok account at any time by:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Disconnecting your TikTok account from within {appName}</li>
                <li>Revoking access through TikTok's app settings (Settings → Security → Manage app permissions)</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Upon revocation, we will delete your TikTok tokens and cease access to your
                TikTok data. Previously scheduled posts that haven't been published will be
                cancelled.
              </p>
            </section>

            {/* Children's Privacy */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                10. Children's Privacy
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Our service is not intended for users under the age of 18. We do not knowingly
                collect personal information from children. If you believe we have collected
                information from a child, please contact us immediately.
              </p>
            </section>

            {/* International Data Transfers */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                11. International Data Transfers
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Your information may be transferred to and processed in countries other than
                your country of residence. These countries may have different data protection
                laws. We ensure appropriate safeguards are in place to protect your information
                in accordance with this Privacy Policy.
              </p>
            </section>

            {/* Third-Party Links */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                12. Third-Party Links
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Our service may contain links to third-party websites, including TikTok.
                We are not responsible for the privacy practices of these external sites.
                We encourage you to review their privacy policies.
              </p>
            </section>

            {/* Changes to Policy */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                13. Changes to This Privacy Policy
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We may update this Privacy Policy from time to time. We will notify you of
                significant changes by posting the new policy on this page and updating the
                "Last updated" date. Your continued use of our service after such changes
                constitutes acceptance of the updated policy.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                14. Contact Us
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                If you have any questions about this Privacy Policy or our data practices,
                please contact us:
              </p>
              <ul className="list-none text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>
                  <strong>Email:</strong>{' '}
                  <a
                    href={`mailto:${contactEmail}`}
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {contactEmail}
                  </a>
                </li>
                <li><strong>Company:</strong> {companyName}</li>
              </ul>
            </section>
          </div>

          {/* Footer Links */}
          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap gap-4 text-sm">
              <Link
                href="/terms"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                Terms of Service
              </Link>
              <span className="text-gray-400">|</span>
              <a
                href="https://www.tiktok.com/legal/privacy-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                TikTok Privacy Policy
              </a>
              <span className="text-gray-400">|</span>
              <a
                href="https://developers.tiktok.com/doc/tiktok-api-v2-terms-of-use"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                TikTok API Terms
              </a>
            </div>
          </div>
        </article>
      </main>

      {/* Page Footer */}
      <footer className="max-w-4xl mx-auto px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>&copy; {new Date().getFullYear()} {companyName}. All rights reserved.</p>
      </footer>
    </div>
  )
}
