import React from 'react';

export default function Terms() {
  return (
    <div className="flex items-center justify-center min-h-screen w-full bg-white mx-[30%]">
      <div className="w-full max-w-6xl bg-white p-8 rounded-lg shadow-lg">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-teal-600">Terms and Conditions</h1>
          <p className="text-sm text-gray-500">Effective Date: April 25, 2025</p>
        </div>
        <div className="space-y-8 px-4 md:px-16">
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Welcome to Edusphere</h2>
            <p className="text-gray-700">
              Thank you for choosing Edusphere! Please read these terms and conditions carefully before using our platform. By accessing or using our services, you agree to be bound by these terms.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Use of the Platform</h2>
            <p className="text-gray-700">
              You agree to use Edusphere responsibly and in compliance with all applicable laws and regulations. Unauthorized use of the platform is strictly prohibited.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Privacy Policy</h2>
            <p className="text-gray-700">
              Your privacy is important to us. Please review our{' '}
              <a href="/privacy-policy" className="text-teal-500 hover:underline">
                Privacy Policy
              </a>{' '}
              to understand how we collect, use, and protect your information.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Limitation of Liability</h2>
            <p className="text-gray-700">
              Edusphere is not liable for any damages resulting from the use of our platform. Use the platform at your own risk.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Changes to Terms</h2>
            <p className="text-gray-700">
              We reserve the right to update these terms at any time. Continued use of the platform after changes are made constitutes your acceptance of the updated terms.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-teal-600 mb-2">Contact Us</h2>
            <p className="text-gray-700">
              If you have any questions about these terms, please contact us at{' '}
              <a href="mailto:support@edusphere.com" className="text-teal-500 hover:underline">
                support@edusphere.com
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}