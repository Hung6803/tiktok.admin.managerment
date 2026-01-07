'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

/**
 * Terms of Service page
 * Required for TikTok Developer App Review compliance
 */
export default function TermsOfServicePage() {
  const lastUpdated = 'January 7, 2026'
  const appName = 'Hagency Media Manager'
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
            Terms of Service
          </h1>
          <p className="text-lg text-gray-700 dark:text-gray-300 mb-2">{appName}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            Last updated: {lastUpdated}
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-6">
            {/* 1. Introduction */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                1. Introduction
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Welcome to {appName} ("we", "our", "the Service").
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                {appName} is a third-party social media management tool that allows users to connect
                their own social media accounts, upload content, schedule posts, and view performance
                data using official platform APIs.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                By accessing or using our Service, you agree to be bound by these Terms of Service.
              </p>
            </section>

            {/* 2. Eligibility */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                2. Eligibility
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You must be at least 18 years old and legally able to enter into a binding agreement
                to use this Service.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                By using {appName}, you confirm that you meet these requirements.
              </p>
            </section>

            {/* 3. Description of Service */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                3. Description of Service
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} provides features including but not limited to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Account authentication via official third-party login systems</li>
                <li>Uploading and publishing user-generated content</li>
                <li>Scheduling and managing posts</li>
                <li>Viewing basic account and content performance information</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                The Service only acts on behalf of users and does not create, modify, or publish
                content without explicit user authorization.
              </p>
            </section>

            {/* 4. Third-Party Platforms Disclaimer */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                4. Third-Party Platforms Disclaimer
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} is an independent third-party application.
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>We are not affiliated with, endorsed by, or officially connected to TikTok or any other social media platform.</li>
                <li>Use of third-party platforms is subject to their own terms and policies.</li>
              </ul>
            </section>

            {/* 5. User Responsibilities */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                5. User Responsibilities
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You agree that:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>You own or have permission to manage the accounts you connect</li>
                <li>You are responsible for all content you upload or publish</li>
                <li>You will not use the Service for unlawful, misleading, or abusive activities</li>
                <li>You will comply with all applicable platform policies and laws</li>
              </ul>
            </section>

            {/* 6. Data Access & Authorization */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                6. Data Access & Authorization
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                When you connect a third-party account, you explicitly authorize us to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Access permitted account information</li>
                <li>Upload or publish content on your behalf</li>
                <li>Store authentication tokens securely for service operation</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                You may revoke access at any time via the connected platform or by contacting us.
              </p>
            </section>

            {/* 7. Intellectual Property */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                7. Intellectual Property
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                All trademarks, logos, and content uploaded by users remain the property of their
                respective owners. {appName} does not claim ownership over user content.
              </p>
            </section>

            {/* 8. Service Availability */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                8. Service Availability
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We strive to maintain uninterrupted service but do not guarantee continuous availability.
                We may modify, suspend, or discontinue features at any time.
              </p>
            </section>

            {/* 9. Limitation of Liability */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                9. Limitation of Liability
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} shall not be liable for:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Content published by users</li>
                <li>Actions taken by third-party platforms</li>
                <li>Loss of data due to platform API changes or service interruptions</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Use of the Service is at your own risk.
              </p>
            </section>

            {/* 10. Termination */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                10. Termination
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We reserve the right to suspend or terminate access if these Terms are violated or
                if required by law or platform policies.
              </p>
            </section>

            {/* 11. Changes to Terms */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                11. Changes to Terms
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We may update these Terms from time to time. Continued use of the Service constitutes
                acceptance of the updated Terms.
              </p>
            </section>

            {/* 12. Contact Information */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                12. Contact Information
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                If you have any questions regarding these Terms, please contact us at:
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
                href="/privacy"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                Privacy Policy
              </Link>
              <span className="text-gray-400">|</span>
              <a
                href="https://www.tiktok.com/legal/terms-of-service"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                TikTok Terms of Service
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
