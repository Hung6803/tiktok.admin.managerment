'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

/**
 * Terms of Service page
 * Required for TikTok Developer App Review compliance
 */
export default function TermsOfServicePage() {
  const lastUpdated = 'December 17, 2025'
  const appName = 'TikTok Manager'
  const companyName = 'TikTok Manager'
  const contactEmail = 'support@tiktokmanager.app'

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
                Welcome to {appName}. These Terms of Service ("Terms") govern your use of our
                social media management platform that integrates with TikTok's API services.
                By accessing or using our service, you agree to be bound by these Terms.
              </p>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                {appName} is a third-party application and is not affiliated with, endorsed by,
                or sponsored by TikTok or ByteDance Ltd. Our service utilizes TikTok's official
                API in accordance with TikTok's Developer Terms of Service.
              </p>
            </section>

            {/* Service Description */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                2. Service Description
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} provides the following services:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Connect and manage multiple TikTok accounts</li>
                <li>Schedule video and photo posts for future publishing</li>
                <li>View account analytics and performance metrics</li>
                <li>Manage content across your TikTok accounts</li>
              </ul>
            </section>

            {/* TikTok Integration */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                3. TikTok Integration & Authorization
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                To use our service, you must authorize {appName} to access your TikTok account
                through TikTok's official OAuth 2.0 authentication flow. By granting this
                authorization, you:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Allow us to access your basic profile information</li>
                <li>Permit us to upload and publish content on your behalf</li>
                <li>Grant access to view your account statistics</li>
                <li>Acknowledge that you can revoke access at any time through TikTok's settings</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
                Your use of TikTok through our service remains subject to{' '}
                <a
                  href="https://www.tiktok.com/legal/terms-of-service"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  TikTok's Terms of Service
                </a>{' '}
                and{' '}
                <a
                  href="https://www.tiktok.com/legal/privacy-policy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Privacy Policy
                </a>.
              </p>
            </section>

            {/* User Responsibilities */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                4. User Responsibilities
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                By using {appName}, you agree to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Provide accurate and complete information</li>
                <li>Maintain the security of your account credentials</li>
                <li>Comply with TikTok's Community Guidelines and Terms of Service</li>
                <li>Not use our service for any illegal or unauthorized purposes</li>
                <li>Not upload content that infringes on intellectual property rights</li>
                <li>Not engage in spam, harassment, or any form of abuse</li>
                <li>Not attempt to circumvent any security measures or rate limits</li>
              </ul>
            </section>

            {/* Content Ownership */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                5. Content Ownership
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You retain all ownership rights to the content you upload through our service.
                By using {appName}, you grant us a limited license to process and transmit your
                content solely for the purpose of providing our services. We do not claim any
                ownership over your content.
              </p>
            </section>

            {/* Prohibited Uses */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                6. Prohibited Uses
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                You may not use {appName} to:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-2">
                <li>Violate any applicable laws or regulations</li>
                <li>Distribute malware, viruses, or harmful code</li>
                <li>Engage in automated data scraping or harvesting</li>
                <li>Impersonate others or misrepresent your identity</li>
                <li>Interfere with or disrupt our services or servers</li>
                <li>Resell or redistribute our services without authorization</li>
              </ul>
            </section>

            {/* Service Availability */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                7. Service Availability
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We strive to maintain reliable service, but we cannot guarantee uninterrupted
                access. Our service depends on TikTok's API availability, and any changes or
                limitations imposed by TikTok may affect our functionality. We reserve the
                right to modify, suspend, or discontinue any part of our service at any time.
              </p>
            </section>

            {/* Limitation of Liability */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                8. Limitation of Liability
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {appName} is provided "as is" without warranties of any kind. We shall not be
                liable for any indirect, incidental, special, consequential, or punitive damages
                arising from your use of our service. This includes, but is not limited to,
                loss of data, loss of profits, or any issues arising from TikTok API changes.
              </p>
            </section>

            {/* Termination */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                9. Termination
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We may terminate or suspend your access to our service immediately, without
                prior notice, for any reason, including breach of these Terms. You may also
                terminate your account at any time by disconnecting your TikTok account and
                ceasing use of our service.
              </p>
            </section>

            {/* Changes to Terms */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                10. Changes to Terms
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                We reserve the right to modify these Terms at any time. We will notify users
                of significant changes by updating the "Last updated" date. Your continued use
                of the service after such modifications constitutes acceptance of the updated Terms.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-8 mb-4">
                11. Contact Us
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                If you have any questions about these Terms of Service, please contact us at:{' '}
                <a
                  href={`mailto:${contactEmail}`}
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {contactEmail}
                </a>
              </p>
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
