"use client";
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { useParams } from 'next/navigation';
import { getApiUrl } from '@/lib/api';

interface AdmissionData {
  academic_year: string;
  total_applicants: number;
  total_admitted: number;
  total_enrolled: number;
  applicants_international: number;
  admitted_international: number;
  enrolled_international: number;
}

interface SchoolDetail {
  institution_id: string;
  name: string;
  admission_data: AdmissionData[];
}

export default function SchoolDetail() {
  const params = useParams();
  const [school, setSchool] = useState<SchoolDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      console.log("Fetching details for ID:", params.id);
      // NEXT_PUBLIC_API_URL đã có /api/v1 rồi, chỉ cần thêm /schools/{id}
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

  if (loading) return <div className="p-10 text-center">Loading...</div>;
  if (!school) return <div className="p-10 text-center">School not found</div>;

  // Lấy dữ liệu năm mới nhất (nếu có nhiều năm)
  const data = school.admission_data.length > 0 ? school.admission_data[0] : null;

  const calcRate = (num: number, den: number) => {
    if (!den || den === 0) return "N/A";
    return ((num / den) * 100).toFixed(1) + "%";
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow overflow-hidden sm:rounded-lg dark:bg-gray-800 mb-6">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-2xl leading-6 font-bold text-gray-900 dark:text-white">
              {school.name}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Common Data Set Analysis (2024-2025)
            </p>
          </div>
        </div>

        {/* Admission Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg dark:bg-gray-800">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Admission Statistics
            </h3>
          </div>
          
          {data ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300">
                      Metric
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300">
                      Total
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-blue-600 uppercase tracking-wider dark:text-blue-400">
                      International
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      Applicants
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {data.total_applicants?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold dark:text-white bg-blue-50 dark:bg-blue-900/20">
                      {data.applicants_international?.toLocaleString() || "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      Admitted
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {data.total_admitted?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold dark:text-white bg-blue-50 dark:bg-blue-900/20">
                      {data.admitted_international?.toLocaleString() || "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      Enrolled
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {data.total_enrolled?.toLocaleString() || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold dark:text-white bg-blue-50 dark:bg-blue-900/20">
                      {data.enrolled_international?.toLocaleString() || "-"}
                    </td>
                  </tr>
                  {/* Acceptance Rate Row */}
                  <tr className="bg-gray-50 dark:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 dark:text-white">
                      Acceptance Rate
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {calcRate(data.total_admitted || 0, data.total_applicants || 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-bold dark:text-blue-400 bg-blue-100 dark:bg-blue-900/40">
                      {calcRate(data.admitted_international || 0, data.applicants_international || 0)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500">No admission data available for this year.</div>
          )}
        </div>
      </main>
    </div>
  );
}

