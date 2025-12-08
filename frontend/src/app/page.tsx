"use client";
import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { getApiUrl } from '@/lib/api';

interface School {
  institution_id: string;
  name: string;
  city_state_zip: string;
  total_applicants?: number;
  total_admitted?: number;
  applicants_international?: number;
  admitted_international?: number;
}

export default function Home() {
  const [schools, setSchools] = useState<School[]>([]);
  const [search, setSearch] = useState('');
  const [letter, setLetter] = useState('');
  const [loading, setLoading] = useState(true);

  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  useEffect(() => {
    const fetchSchools = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (search) params.append('q', search);
        if (letter) params.append('letter', letter);
        
        // NEXT_PUBLIC_API_URL đã có /api/v1 rồi, chỉ cần thêm /schools
        const url = `${getApiUrl('/schools')}?${params.toString()}`;
        console.log("Fetching schools:", url);
        
        const res = await fetch(url);
        console.log("API Status:", res.status);
        
        if (res.ok) {
          const data = await res.json();
          console.log("Schools data length:", data.length);
          if (data.length > 0) console.log("First school:", data[0]);
          setSchools(data);
        } else {
          console.error("API Error:", res.status, res.statusText);
        }
      } catch (error) {
        console.error("Lỗi tải danh sách trường:", error);
      } finally {
        setLoading(false);
      }
    };

    const timeoutId = setTimeout(() => {
      fetchSchools();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [search, letter]);

  const calcRate = (num?: number, den?: number) => {
    if (!num || !den || den === 0) return "-";
    return ((num / den) * 100).toFixed(1) + "%";
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search for a university..."
              className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:border-gray-700"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setLetter('');
              }}
            />
          </div>

          <div className="flex flex-wrap gap-2 mb-8 justify-center">
            <button
              onClick={() => { setLetter(''); setSearch(''); }}
              className={`px-3 py-1 rounded text-sm font-medium ${!letter ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
            >
              ALL
            </button>
            {alphabet.map((char) => (
              <button
                key={char}
                onClick={() => { setLetter(char); setSearch(''); }}
                className={`px-3 py-1 rounded text-sm font-medium ${letter === char ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              >
                {char}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-10">Loading...</div>
          ) : (
            <div className="bg-white shadow overflow-hidden border-b border-gray-200 sm:rounded-lg dark:bg-gray-800 dark:border-gray-700">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300">
                        School Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300">
                        TTL Apps
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300">
                        TTL Rate
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-blue-600 uppercase tracking-wider dark:text-blue-400">
                        INT Apps
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-blue-600 uppercase tracking-wider dark:text-blue-400">
                        INT Admit
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-blue-600 uppercase tracking-wider dark:text-blue-400">
                        INT Rate
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
                    {schools.map((school) => (
                      <tr key={school.institution_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <Link href={`/school/${school.institution_id}`} className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">
                            {school.name}
                          </Link>
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                            {school.city_state_zip}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-300">
                          {school.total_applicants?.toLocaleString() || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-white font-medium">
                          {calcRate(school.total_admitted, school.total_applicants)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-300 bg-blue-50/30 dark:bg-blue-900/10">
                          {school.applicants_international?.toLocaleString() || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-300 bg-blue-50/30 dark:bg-blue-900/10">
                          {school.admitted_international?.toLocaleString() || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-blue-600 dark:text-blue-400 bg-blue-50/30 dark:bg-blue-900/10">
                          {calcRate(school.admitted_international, school.applicants_international)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {schools.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                  No schools found matching your criteria.
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
