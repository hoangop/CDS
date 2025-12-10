"use client";
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { useParams } from 'next/navigation';
import { getApiUrl } from '@/lib/api';
import Link from 'next/link';

interface AdmissionData {
  academic_year: string;
  total_applicants?: number;
  total_admitted?: number;
  total_enrolled?: number;
  applicants_international?: number;
  admitted_international?: number;
  enrolled_international?: number;
}

interface SchoolDetail {
  institution_id: string;
  name: string;
  city_state_zip?: string;
  website_url?: string;
  rank_2025?: number;
  rank_type?: string;
  admission_data: AdmissionData[];
}

export default function SchoolDetail() {
  const params = useParams();
  const [school, setSchool] = useState<SchoolDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      console.log("Fetching details for ID:", params.id);
      fetch(getApiUrl(`/schools/${params.id}`))
        .then(res => res.json())
        .then(data => {
          console.log("School Detail Data:", data);
          setSchool(data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [params.id]);

  const calcRate = (num?: number, den?: number) => {
    if (!num || !den || den === 0) return "-";
    return ((num / den) * 100).toFixed(1) + "%";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Navbar />
        <div className="text-center py-20">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
          <p className="mt-4 text-slate-600">Loading institution details...</p>
        </div>
      </div>
    );
  }

  if (!school) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Navbar />
        <div className="text-center py-20">
          <h2 className="text-2xl font-bold text-slate-800">Institution not found</h2>
          <Link href="/" className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">
            ← Back to All Institutions
          </Link>
        </div>
      </div>
    );
  }

  // Lấy dữ liệu năm mới nhất
  const latestData = school.admission_data.length > 0 ? school.admission_data[0] : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      
      <main className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <div className="mb-6">
          <Link 
            href="/" 
            className="inline-flex items-center text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to All Institutions
          </Link>
        </div>

        {/* School Header Card */}
        <div className="bg-white shadow-lg rounded-2xl overflow-hidden mb-8 border border-slate-200">
          <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-8 py-6">
            <h1 className="text-3xl font-serif font-bold text-white mb-2">
              {school.name}
            </h1>
            {school.city_state_zip && (
              <p className="text-indigo-100 text-sm">
                📍 {school.city_state_zip}
              </p>
            )}
            {school.website_url && (
              <a 
                href={school.website_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-indigo-100 hover:text-white text-sm inline-flex items-center mt-2 transition-colors"
              >
                🌐 Visit Website
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}
          </div>

          {/* Ranking Info */}
          <div className="px-8 py-6 bg-gradient-to-r from-amber-50 to-yellow-50 border-t border-amber-200">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-sm text-slate-600 mb-1">U.S. News Ranking (2025)</p>
                {school.rank_2025 ? (
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center px-4 py-2 rounded-full bg-amber-500 text-white font-bold text-2xl shadow-md">
                      #{school.rank_2025}
                    </span>
                    <span className="text-slate-700 font-semibold">
                      {school.rank_type || "Category unavailable"}
                    </span>
                  </div>
                ) : (
                  <span className="text-slate-500 italic">Ranking not available</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Admission Statistics Table */}
        <div className="bg-white shadow-lg rounded-2xl overflow-hidden border border-slate-200">
          <div className="px-6 py-4 bg-gradient-to-r from-slate-100 to-slate-50 border-b border-slate-200">
            <h2 className="text-xl font-serif font-bold text-slate-800">
              Admission Statistics
            </h2>
            {latestData && (
              <p className="text-sm text-slate-600 mt-1">
                Academic Year: {latestData.academic_year}
              </p>
            )}
          </div>
          
          {latestData ? (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-cyan-600">
                  <tr>
                    <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-white">
                      Metric
                    </th>
                    <th scope="col" className="px-6 py-4 text-right text-sm font-semibold text-white">
                      Total
                    </th>
                    <th scope="col" className="px-6 py-4 text-right text-sm font-semibold text-white border-l-2 border-cyan-700">
                      International
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {/* Applicants */}
                  <tr className="bg-white hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      Applicants
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                      {latestData.total_applicants?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-blue-700 border-l-2 border-gray-200 bg-blue-50/30">
                      {latestData.applicants_international?.toLocaleString() || "-"}
                    </td>
                  </tr>

                  {/* Admitted */}
                  <tr className="bg-gray-50 hover:bg-gray-100 transition-colors">
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      Admitted
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                      {latestData.total_admitted?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-blue-700 border-l-2 border-gray-200 bg-blue-50/30">
                      {latestData.admitted_international?.toLocaleString() || "-"}
                    </td>
                  </tr>

                  {/* Enrolled */}
                  <tr className="bg-white hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      Enrolled
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                      {latestData.total_enrolled?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-blue-700 border-l-2 border-gray-200 bg-blue-50/30">
                      {latestData.enrolled_international?.toLocaleString() || "-"}
                    </td>
                  </tr>

                  {/* Acceptance Rate - Highlighted */}
                  <tr className="bg-gradient-to-r from-emerald-50 to-green-50 border-t-2 border-emerald-200">
                    <td className="px-6 py-5 text-sm font-bold text-gray-900">
                      Acceptance Rate
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-right text-lg font-bold text-emerald-700">
                      {calcRate(latestData.total_admitted, latestData.total_applicants)}
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-right text-lg font-bold text-blue-700 border-l-2 border-emerald-200 bg-blue-100/50">
                      {calcRate(latestData.admitted_international, latestData.applicants_international)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-16 text-center">
              <svg className="mx-auto h-12 w-12 text-slate-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-slate-500 text-lg font-medium">No admission data available</p>
              <p className="text-slate-400 text-sm mt-1">This institution has not reported CDS data yet</p>
            </div>
          )}
        </div>

        {/* Year-over-Year Data (if multiple years) */}
        {school.admission_data.length > 1 && (
          <div className="mt-8 bg-white shadow-lg rounded-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 bg-gradient-to-r from-slate-100 to-slate-50 border-b border-slate-200">
              <h2 className="text-xl font-serif font-bold text-slate-800">
                Historical Data
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-cyan-600">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-white">Year</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white">Total Apps</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white">Total Admit</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white">Rate</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white border-l-2 border-cyan-700">Int'l Apps</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white">Int'l Admit</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-white">Int'l Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {school.admission_data.map((yearData, idx) => (
                    <tr key={yearData.academic_year} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                        {yearData.academic_year}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-700">
                        {yearData.total_applicants?.toLocaleString() || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-700">
                        {yearData.total_admitted?.toLocaleString() || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-emerald-700">
                        {calcRate(yearData.total_admitted, yearData.total_applicants)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-blue-700 border-l-2 border-gray-200 bg-blue-50/30">
                        {yearData.applicants_international?.toLocaleString() || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-blue-700 bg-blue-50/30">
                        {yearData.admitted_international?.toLocaleString() || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-blue-800 bg-blue-50/30">
                        {calcRate(yearData.admitted_international, yearData.applicants_international)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-slate-500 text-sm">
        <p>© 2024 CDS Analytics. Data sourced from institutional Common Data Set reports.</p>
      </footer>
    </div>
  );
}
