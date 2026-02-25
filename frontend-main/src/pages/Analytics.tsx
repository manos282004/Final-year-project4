import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import BusinessTypeSelector from '../components/BusinessTypeSelector';
import { apiService, AnalyticsData } from '../services/api';

export default function Analytics() {
  const [selectedBusinessType, setSelectedBusinessType] = useState('showroom');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    if (selectedBusinessType) {
      loadAnalytics();
    }
  }, [selectedBusinessType]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getAnalytics(selectedBusinessType);
      setAnalyticsData(data);
    } catch (err) {
      setError('Unable to load analytics data. Please ensure backend is running.');
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = analyticsData
    ? analyticsData.categories.map((category, index) => ({
        name: category,
        demand: analyticsData.demand[index],
        growth: analyticsData.growth[index],
      }))
    : [];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center space-x-3 mb-6">
          <TrendingUp className="w-8 h-8 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-800">Business Analytics</h2>
        </div>
        <BusinessTypeSelector
          selectedType={selectedBusinessType}
          onSelectType={setSelectedBusinessType}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Connection Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-6">Demand vs Growth Comparison</h3>

          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  style={{ fontSize: '14px' }}
                />
                <YAxis
                  stroke="#6b7280"
                  style={{ fontSize: '14px' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="circle"
                />
                <Bar
                  dataKey="demand"
                  fill="url(#colorDemand)"
                  radius={[8, 8, 0, 0]}
                  animationDuration={1000}
                  animationBegin={0}
                />
                <Bar
                  dataKey="growth"
                  fill="url(#colorGrowth)"
                  radius={[8, 8, 0, 0]}
                  animationDuration={1000}
                  animationBegin={200}
                />
                <defs>
                  <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0.8} />
                  </linearGradient>
                  <linearGradient id="colorGrowth" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#059669" stopOpacity={0.8} />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-20">
              <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                Connect to backend to view analytics data
              </p>
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
              <h4 className="text-lg font-bold text-blue-900 mb-2">Demand Analysis</h4>
              <p className="text-blue-700 text-sm">
                Represents current market demand for your business type across different regions and customer segments.
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
              <h4 className="text-lg font-bold text-green-900 mb-2">Growth Potential</h4>
              <p className="text-green-700 text-sm">
                Indicates projected growth opportunities based on market trends, competition analysis, and regional factors.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
