'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

/**
 * Privacy Policy page
 * Required for TikTok Developer App Review compliance
 */
export default function PrivacyPolicyPage() {
  const lastUpdated = 'January 7, 2026'
  const appName = 'Operis Media Manager'
  const contactEmail = 'support@operis.vn'
  const website = 'https://media.operis.vn'

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
          <p className="text-lg text-gray-700 dark:text-gray-300 mb-2">{appName}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            Last updated: {lastUpdated}
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-6">
            {/* 1. Overview */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                1. Overview
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                This Privacy Policy explains how {appName} collects, uses, stores, and protects user data.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                We are committed to protecting your privacy and handling data responsibly.
              </p>
            </section>

            {/* 2. Information We Collect */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                2. Information We Collect
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We may collect the following types of information:
              </p>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                a. Account Information
              </h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li>User ID (provided by third-party platforms)</li>
                <li>Display name</li>
                <li>Profile image (avatar)</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                b. Authentication Data
              </h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li>Access tokens and refresh tokens issued by third-party platforms</li>
                <li>Tokens are stored securely and encrypted and are used only to provide the Service</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mt-6 mb-3">
                c. Content Data
              </h3>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li>Videos or media files uploaded by users</li>
                <li>Post metadata (captions, publish status, timestamps)</li>
              </ul>
            </section>

            {/* 3. How We Use Your Information */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                3. How We Use Your Information
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We use collected data solely to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Authenticate users</li>
                <li>Upload and publish content on behalf of users</li>
                <li>Display account and content information</li>
                <li>Improve service reliability and performance</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4 font-medium">
                We do not sell, rent, or share user data for advertising or marketing purposes.
              </p>
            </section>

            {/* 4. Third-Party Platforms */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                4. Third-Party Platforms
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} accesses third-party platforms only through official APIs and within
                the scopes explicitly authorized by users.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Use of those platforms is governed by their own privacy policies.
              </p>
            </section>

            {/* 5. Data Storage & Security */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                5. Data Storage & Security
              </h2>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
                <li>All sensitive data is encrypted at rest and in transit</li>
                <li>Access to user data is restricted to authorized systems only</li>
                <li>We follow industry-standard security practices</li>
              </ul>
            </section>

            {/* 6. Data Retention */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                6. Data Retention
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                User data is retained only as long as necessary to provide the Service or comply
                with legal obligations.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Users may request deletion of their data at any time.
              </p>
            </section>

            {/* 7. User Rights */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                7. User Rights
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You have the right to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Access your data</li>
                <li>Request correction or deletion</li>
                <li>Revoke third-party authorization</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Requests can be sent to our support email.
              </p>
            </section>

            {/* 8. Children's Privacy */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                8. Children's Privacy
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} is not intended for users under 18 years old.
                We do not knowingly collect data from minors.
              </p>
            </section>

            {/* 9. Changes to This Policy */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                9. Changes to This Policy
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We may update this Privacy Policy periodically. Updates will be posted on this page.
              </p>
            </section>

            {/* 10. Contact Us */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                10. Contact Us
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                If you have questions or concerns about this Privacy Policy, contact us at:
              </p>
              <ul className="list-none text-gray-600 dark:text-gray-300 mt-4 space-y-2">
                <li>
                  <strong>Email:</strong>{' '}
                  <a
                    href={`mailto:${contactEmail}`}
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {contactEmail}
                  </a>
                </li>
                <li>
                  <strong>Website:</strong>{' '}
                  <a
                    href={website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {website}
                  </a>
                </li>
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
            </div>
          </div>
        </article>
      </main>

      {/* Page Footer */}
      <footer className="max-w-4xl mx-auto px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>&copy; {new Date().getFullYear()} {appName}. All rights reserved.</p>
      </footer>
    </div>
  )
}
