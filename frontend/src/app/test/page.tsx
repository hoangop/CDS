"use client";

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-8">
      <h1 className="text-4xl font-bold text-slate-800 mb-4">CSS Test Page</h1>
      
      {/* Test Cyan Colors */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Test 1: Cyan Background</h2>
        <div className="bg-cyan-600 text-white p-4 rounded">
          This should have TEAL/CYAN background
        </div>
      </div>

      {/* Test Gray Colors */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Test 2: Gray Backgrounds</h2>
        <div className="bg-white p-4 mb-2">White background</div>
        <div className="bg-gray-50 p-4 mb-2">Gray-50 background</div>
        <div className="bg-gray-100 p-4 mb-2">Gray-100 background</div>
      </div>

      {/* Test Table */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Test 3: Table</h2>
        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-cyan-600">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-white">
                  Column 1
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-white">
                  Column 2
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr className="bg-white hover:bg-gray-100">
                <td className="px-6 py-4">Row 1, Cell 1</td>
                <td className="px-6 py-4 text-center">Row 1, Cell 2</td>
              </tr>
              <tr className="bg-gray-50 hover:bg-gray-100">
                <td className="px-6 py-4">Row 2, Cell 1</td>
                <td className="px-6 py-4 text-center">Row 2, Cell 2</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Diagnostic Info */}
      <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4">
        <h2 className="text-xl font-semibold mb-2">Diagnostic Info:</h2>
        <ul className="list-disc list-inside">
          <li>If you see COLORS → Tailwind CSS is working</li>
          <li>If you see ONLY BLACK/WHITE → Tailwind CSS NOT loaded</li>
          <li>Check browser DevTools → Elements → Styles to see CSS</li>
        </ul>
      </div>
    </div>
  );
}

