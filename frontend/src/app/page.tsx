"use client";
import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { getApiUrl } from '@/lib/api';

interface School {
  institution_id: string;
  name: string;
  city_state_zip: string;
  rank_2025?: number;
  rank_type?: string;
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
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  useEffect(() => {
    const fetchSchools = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (search) params.append('q', search);
        if (letter) params.append('letter', letter);
        params.append('limit', '1000'); // Lấy tất cả để phân trang ở client
        
        const url = `${getApiUrl('/schools')}?${params.toString()}`;
        console.log("Fetching schools:", url);
        
        const res = await fetch(url);
        console.log("API Status:", res.status);
        
        if (res.ok) {
          const data = await res.json();
          console.log("Schools data length:", data.length);
          setSchools(data);
          setCurrentPage(1); // Reset về trang 1 khi search/filter mới
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

  // Phân trang
  const totalPages = Math.ceil(schools.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentSchools = schools.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      
      <main className="max-w-[1400px] mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-serif font-bold text-slate-800 mb-2">
              University Common Data Set
            </h1>
            <p className="text-slate-600">Comprehensive admission statistics and rankings</p>
          </div>

          {/* Search Box */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search for a university..."
              className="w-full px-6 py-3 rounded-xl border-2 border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all shadow-sm bg-white"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setLetter('');
              }}
            />
          </div>

          {/* Alphabet Filter */}
          <div className="flex flex-wrap gap-2 mb-8 justify-center">
            <button
              onClick={() => { setLetter(''); setSearch(''); }}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                !letter 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              ALL
            </button>
            {alphabet.map((char) => (
              <button
                key={char}
                onClick={() => { setLetter(char); setSearch(''); }}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  letter === char 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {char}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
              <p className="mt-4 text-slate-600">Loading institutions...</p>
            </div>
          ) : (
            <>
              {/* Results Info */}
              <div className="mb-4 text-sm text-slate-600 flex justify-between items-center">
                <span>
                  Showing {startIndex + 1}-{Math.min(endIndex, schools.length)} of {schools.length} institutions
                </span>
                <span className="text-indigo-600 font-medium">Page {currentPage} of {totalPages}</span>
              </div>

              {/* Table */}
              <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-slate-200">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-gradient-to-r from-slate-700 to-slate-800">
                      <tr>
                        <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">
                          Institution Name
                        </th>
                        <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-amber-300 uppercase tracking-wider">
                          Rank
                        </th>
                        <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-amber-300 uppercase tracking-wider">
                          Rank Type
                        </th>
                        <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-emerald-300 uppercase tracking-wider">
                          Overall Rate
                        </th>
                        <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-blue-300 uppercase tracking-wider">
                          Int'l Rate
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {currentSchools.map((school, idx) => (
                        <tr 
                          key={school.institution_id} 
                          className={`hover:bg-indigo-50 transition-colors ${
                            idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                          }`}
                        >
                          <td className="px-6 py-4 text-sm">
                            <Link 
                              href={`/school/${school.institution_id}`} 
                              className="font-semibold text-indigo-700 hover:text-indigo-900 hover:underline transition-colors"
                            >
                              {school.name}
                            </Link>
                            <div className="text-xs text-slate-500 mt-1 truncate max-w-[300px]">
                              {school.city_state_zip || "Location unavailable"}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold">
                            {school.rank_2025 ? (
                              <span className="inline-flex items-center px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-semibold">
                                #{school.rank_2025}
                              </span>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-left">
                            <span className="text-slate-600 font-medium text-xs">
                              {school.rank_type || "-"}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-emerald-700">
                            {calcRate(school.total_admitted, school.total_applicants)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-blue-700 bg-blue-50/50">
                            {calcRate(school.admitted_international, school.applicants_international)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {schools.length === 0 && (
                  <div className="text-center py-16 text-slate-500">
                    <svg className="mx-auto h-12 w-12 text-slate-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-lg font-medium">No institutions found</p>
                    <p className="text-sm mt-1">Try adjusting your search criteria</p>
                  </div>
                )}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-8 flex justify-center items-center gap-2">
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    ← Previous
                  </button>
                  
                  <div className="flex gap-1">
                    {/* First page */}
                    {currentPage > 3 && (
                      <>
                        <button
                          onClick={() => goToPage(1)}
                          className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-all"
                        >
                          1
                        </button>
                        {currentPage > 4 && <span className="px-2 py-2 text-slate-400">...</span>}
                      </>
                    )}
                    
                    {/* Page numbers around current */}
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                      .filter(page => page >= currentPage - 2 && page <= currentPage + 2)
                      .map(page => (
                        <button
                          key={page}
                          onClick={() => goToPage(page)}
                          className={`px-4 py-2 rounded-lg font-medium transition-all ${
                            page === currentPage
                              ? 'bg-indigo-600 text-white shadow-md'
                              : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    
                    {/* Last page */}
                    {currentPage < totalPages - 2 && (
                      <>
                        {currentPage < totalPages - 3 && <span className="px-2 py-2 text-slate-400">...</span>}
                        <button
                          onClick={() => goToPage(totalPages)}
                          className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-all"
                        >
                          {totalPages}
                        </button>
                      </>
                    )}
                  </div>
                  
                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-slate-500 text-sm">
        <p>© 2024 CDS Analytics. Data sourced from institutional Common Data Set reports.</p>
      </footer>
    </div>
  );
}
